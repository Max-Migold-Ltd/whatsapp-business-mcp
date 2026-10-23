// WhatsApp linked-device session stored in PostgreSQL, so it survives container redeploys.
// Same format as Baileys' useMultiFileAuthState (one record per file), in a table instead of files.
//
// The session is a login credential for the WhatsApp number: anyone with this table can act as it.

import pg from 'pg'
import { BufferJSON, initAuthCreds, proto } from '@whiskeysockets/baileys'

const TABLE = 'wa_auth'

export async function usePostgresAuthState(connectionString) {
  const pool = new pg.Pool({ connectionString, max: 3 })
  await pool.query(`CREATE TABLE IF NOT EXISTS ${TABLE} (id TEXT PRIMARY KEY, data TEXT NOT NULL)`)

  const read = async (id) => {
    const { rows } = await pool.query(`SELECT data FROM ${TABLE} WHERE id = $1`, [id])
    return rows.length ? JSON.parse(rows[0].data, BufferJSON.reviver) : null
  }
  const write = (id, value) =>
    pool.query(
      `INSERT INTO ${TABLE} (id, data) VALUES ($1, $2) ON CONFLICT (id) DO UPDATE SET data = EXCLUDED.data`,
      [id, JSON.stringify(value, BufferJSON.replacer)],
    )
  const remove = (id) => pool.query(`DELETE FROM ${TABLE} WHERE id = $1`, [id])

  const creds = (await read('creds')) || initAuthCreds()

  return {
    state: {
      creds,
      keys: {
        get: async (type, ids) => {
          const data = {}
          await Promise.all(
            ids.map(async (id) => {
              let value = await read(`${type}-${id}`)
              if (type === 'app-state-sync-key' && value) {
                value = proto.Message.AppStateSyncKeyData.fromObject(value)
              }
              data[id] = value
            }),
          )
          return data
        },
        set: async (data) => {
          const tasks = []
          for (const category in data) {
            for (const id in data[category]) {
              const value = data[category][id]
              tasks.push(value ? write(`${category}-${id}`, value) : remove(`${category}-${id}`))
            }
          }
          await Promise.all(tasks)
        },
      },
    },
    saveCreds: () => write('creds', creds),
    clear: () => pool.query(`DELETE FROM ${TABLE}`),
  }
}
