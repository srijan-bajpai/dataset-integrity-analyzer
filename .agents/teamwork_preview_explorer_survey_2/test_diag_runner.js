const { execFile } = require('child_process');
const path = require('path');
const fileUrl = 'file:///' + path.resolve(__dirname, 'test_diagnostics.html').replace(/\\/g, '/');

execFile('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
  '--headless=new',
  '--dump-dom',
  '--no-sandbox',
  fileUrl
], { maxBuffer: 10 * 1024 * 1024 }, (err, stdout, stderr) => {
  if (err) {
    console.error('Execution error:', err);
    return;
  }
  const match = stdout.match(/<div id="diagnostics-bridge"[^>]*>([\s\S]*?)<\/div>/);
  if (match) {
    console.log('DIAGNOSTICS EXTRACTED:\n', JSON.stringify(JSON.parse(match[1]), null, 2));
  } else {
    console.log('No diagnostics match found');
  }
});
