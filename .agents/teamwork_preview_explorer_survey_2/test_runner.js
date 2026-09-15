const { execFile } = require('child_process');
const path = require('path');
const fileUrl = 'file:///' + path.resolve(__dirname, 'test_inline.html').replace(/\\/g, '/');
console.log('Testing URL:', fileUrl);

execFile('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
  '--headless=new',
  '--dump-dom',
  '--no-sandbox',
  '--disable-web-security',
  fileUrl
], { maxBuffer: 10 * 1024 * 1024 }, (err, stdout, stderr) => {
  if (err) {
    console.error('Execution error:', err);
    return;
  }
  const match = stdout.match(/<div id="status">([\s\S]*?)<\/div>/);
  console.log('EXTRACTED STATUS:', match ? match[1] : 'No status match found');
});
