const { spawn } = require('child_process');
const path = require('path');

const viteBin = path.join(__dirname, 'node_modules', 'vite', 'bin', 'vite.js');
const child = spawn(process.execPath, [viteBin, '--port', '3000'], {
  cwd: __dirname,
  stdio: 'inherit'
});

child.on('exit', (code) => process.exit(code));
