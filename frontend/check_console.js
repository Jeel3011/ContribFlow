const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('BROWSER ERROR:', msg.text());
    }
  });
  
  page.on('pageerror', exception => {
    console.log('PAGE ERROR:', exception);
  });

  try {
    await page.goto('http://localhost:5173', { timeout: 5000 });
    await page.waitForTimeout(2000); // wait for render
  } catch (e) {
    console.log('Navigation failed:', e.message);
  }

  await browser.close();
})();
