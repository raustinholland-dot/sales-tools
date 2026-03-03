/**
 * Gemini Conversation Exporter
 *
 * HOW TO USE:
 * 1. Open a Gemini conversation at gemini.google.com
 * 2. Scroll to the TOP of the conversation (so all messages lazy-load)
 * 3. Wait for all messages to finish loading (no spinner visible)
 * 4. Open DevTools (Cmd+Option+I on Mac)
 * 5. Paste this entire script into the Console tab and press Enter
 * 6. The transcript is copied to your clipboard automatically
 * 7. Paste into a .txt file named: YYYY-MM-DD_deal-name_topic.txt
 *    e.g.: 2026-01-15_velentium_initial-discovery.txt
 * 8. Save to: deal-intelligence-engine/backfill/<deal-name>/
 *
 * DEAL NAME MAPPING (use these exact folder names):
 *   velentium       → Velentium Medical
 *   panthrrx        → PantherRX Rare
 *   paradigm        → Paradigm Health
 *   frhc            → Family Resource Home Care
 *   rcs             → RCS (vCISO deal)
 *   msu             → Michigan State University
 *   (add others as needed)
 */

(async function exportGeminiConversation() {

  // Step 1: Attempt to scroll to top to trigger lazy loading
  const scrollContainer =
    document.querySelector('[data-test-id="chat-history-container"]') ||
    document.querySelector('chat-window') ||
    document.querySelector('main') ||
    document.documentElement;

  console.log('Scrolling to top to trigger full message load...');
  scrollContainer.scrollTop = 0;
  window.scrollTo(0, 0);

  // Step 2: Wait for any lazy-load spinner to appear and disappear
  const waitForLoad = () => new Promise(resolve => {
    let attempts = 0;
    const check = () => {
      const spinner = document.querySelector('mat-progress-bar.mdc-linear-progress--indeterminate');
      if (spinner) {
        // Spinner visible — still loading, keep waiting
        attempts = 0;
        setTimeout(check, 300);
      } else {
        attempts++;
        if (attempts >= 5) {
          // No spinner for 5 consecutive checks (~1.5s) — done loading
          resolve();
        } else {
          setTimeout(check, 300);
        }
      }
    };
    setTimeout(check, 500);
  });

  await waitForLoad();
  console.log('Messages loaded. Extracting...');

  // Step 3: Extract all conversation turns
  const turns = document.querySelectorAll('user-query, model-response');

  if (!turns.length) {
    console.error('No conversation turns found. Make sure you are on a gemini.google.com/app/... page with an open conversation.');
    return;
  }

  // Step 4: Get conversation title
  const title = document.title.replace(/^Gemini\s*[-–]\s*/i, '').trim() || 'untitled';
  const date = new Date().toISOString().split('T')[0];
  const url = window.location.href;

  const lines = [];
  lines.push(`GEMINI CONVERSATION EXPORT`);
  lines.push(`Title: ${title}`);
  lines.push(`Exported: ${date}`);
  lines.push(`URL: ${url}`);
  lines.push(`Turns: ${turns.length}`);
  lines.push(`${'='.repeat(60)}`);
  lines.push('');

  let turnCount = 0;

  for (const turn of turns) {
    const tag = turn.tagName.toLowerCase();

    if (tag === 'user-query') {
      // Try multiple selectors for user message text
      const contentEl =
        turn.querySelector('div.query-content') ||
        turn.querySelector('.query-text') ||
        turn.querySelector('.query-text-line') ||
        turn;
      const text = contentEl.innerText.trim();
      if (text) {
        lines.push(`--- AUSTIN ---`);
        lines.push(text);
        lines.push('');
        turnCount++;
      }

    } else if (tag === 'model-response') {
      // Try multiple selectors for Gemini response text
      const contentEl =
        turn.querySelector('message-content .markdown') ||
        turn.querySelector('message-content') ||
        turn.querySelector('.markdown') ||
        turn;
      const text = contentEl.innerText.trim();
      if (text) {
        lines.push(`--- GEMINI ---`);
        lines.push(text);
        lines.push('');
        turnCount++;
      }
    }
  }

  lines.push(`${'='.repeat(60)}`);
  lines.push(`END OF EXPORT — ${turnCount} message turns captured`);

  const output = lines.join('\n');

  // Step 5: Copy to clipboard
  try {
    await navigator.clipboard.writeText(output);
    console.log(`✅ Copied ${turnCount} turns to clipboard!`);
    console.log(`📋 Paste into: deal-intelligence-engine/backfill/<deal-name>/${date}_<topic>.txt`);
  } catch (e) {
    console.warn('Clipboard write failed — copy the output below manually:');
    console.log(output);
  }

  // Also return the output in case you want to inspect it
  return output;

})();
