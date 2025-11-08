module.exports = {
  apps: [{
    name: 'ki-smart-home',
    script: 'main.py',
    args: 'web --host 0.0.0.0 --port 8080',
    interpreter: './venv/bin/python3',

    // Instances
    instances: 1,
    exec_mode: 'fork',

    // Auto-restart
    autorestart: true,
    watch: false,
    max_memory_restart: '500M',

    // Restart delay
    restart_delay: 4000,
    min_uptime: '10s',
    max_restarts: 10,

    // Logs
    error_file: './logs/pm2-error.log',
    out_file: './logs/pm2-out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss',
    merge_logs: true,

    // Environment
    env: {
      NODE_ENV: 'production',
      PYTHONUNBUFFERED: '1'
    },

    // Advanced
    listen_timeout: 10000,
    kill_timeout: 5000,
    wait_ready: false,

    // Cron restart (täglich um 4:00 Uhr)
    cron_restart: '0 4 * * *'
  }]
};
