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
    
    // Fill the input
    await page.fill('input[placeholder="https://github.com/owner/repo"]', 'https://github.com/Tracer-Cloud/opensre');
    
    // Click the button
    await page.click('text=Run Analysis');
    
    // Wait for a bit
    await page.waitForTimeout(3000);
    
  } catch (e) {
    console.log('Test failed:', e.message);
  }

  await browser.close();
})();
