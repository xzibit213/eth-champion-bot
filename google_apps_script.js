/**
 * ETH Champion Bot — Google Apps Script Webhook
 * 
 * SINGLE-ROW-PER-TRADE architecture:
 *   OPENED  → Creates a new row with entry details, light orange background.
 *   CLOSED  → Finds the matching OPENED row, fills in exit details,
 *             colors the row green (TP) or red (SL).
 *
 * Sheet columns (A–N):
 *   A: #       (Trade number)
 *   B: Symbol
 *   C: Direction
 *   D: Entry Price
 *   E: SL Price
 *   F: TP Price
 *   G: Open Time
 *   H: Exit Price
 *   I: Close Time
 *   J: Duration
 *   K: Candles
 *   L: Result (TP / SL)
 *   M: Return %
 *   N: Balance After
 *
 * DEPLOYMENT:
 *   1. Open your Google Sheet → Extensions → Apps Script
 *   2. Delete any existing code and paste this entire file.
 *   3. Click Deploy → New Deployment → Web App
 *   4. Set "Execute as" = Me, "Who has access" = Anyone
 *   5. Click Deploy and copy the URL into your Render env var GOOGLE_WEBHOOK_URL
 */

function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName("Trade Ledger") || ss.getActiveSheet();
    
    if (data.event === "OPENED") {
      handleOpened(sheet, data);
    } else if (data.event === "CLOSED") {
      handleClosed(sheet, data);
    }
    
    return ContentService.createTextOutput(JSON.stringify({ status: "ok" }))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ status: "error", message: err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function handleOpened(sheet, data) {
  // Ensure headers exist
  if (sheet.getLastRow() === 0) {
    var headers = ["#", "Symbol", "Direction", "Entry Price", "SL Price", "TP Price", 
                   "Open Time", "Exit Price", "Close Time", "Duration", "Candles", 
                   "Result", "Return %", "Balance After"];
    sheet.appendRow(headers);
    var headerRange = sheet.getRange(1, 1, 1, headers.length);
    headerRange.setBackground("#1a1a2e");
    headerRange.setFontColor("#ffffff");
    headerRange.setFontWeight("bold");
    headerRange.setHorizontalAlignment("center");
    sheet.setFrozenRows(1);
    
    // Set column widths
    sheet.setColumnWidth(1, 40);   // #
    sheet.setColumnWidth(2, 100);  // Symbol
    sheet.setColumnWidth(3, 80);   // Direction
    sheet.setColumnWidth(4, 100);  // Entry
    sheet.setColumnWidth(5, 100);  // SL
    sheet.setColumnWidth(6, 100);  // TP
    sheet.setColumnWidth(7, 170);  // Open Time
    sheet.setColumnWidth(8, 100);  // Exit Price
    sheet.setColumnWidth(9, 170);  // Close Time
    sheet.setColumnWidth(10, 80);  // Duration
    sheet.setColumnWidth(11, 70);  // Candles
    sheet.setColumnWidth(12, 70);  // Result
    sheet.setColumnWidth(13, 90);  // Return %
    sheet.setColumnWidth(14, 110); // Balance
  }
  
  var tradeNum = sheet.getLastRow(); // Row count minus header = trade number
  var newRow = [
    tradeNum,                        // #
    data.symbol || "ETH/USDT",       // Symbol
    data.direction || "",            // Direction
    data.entry_price || "",          // Entry Price
    data.sl_price || "",             // SL Price
    data.tp_price || "",             // TP Price
    data.open_timestamp || "",       // Open Time
    "—",                             // Exit Price (pending)
    "—",                             // Close Time (pending)
    "ACTIVE",                        // Duration (pending)
    "—",                             // Candles (pending)
    "ACTIVE",                        // Result (pending)
    "—",                             // Return % (pending)
    "$" + parseFloat(data.current_balance || 0).toFixed(2)  // Balance
  ];
  
  sheet.appendRow(newRow);
  
  // Color the entire row light orange to indicate active trade
  var rowNum = sheet.getLastRow();
  var range = sheet.getRange(rowNum, 1, 1, 14);
  range.setBackground("#fff3e0");       // Light orange
  range.setFontColor("#333333");
  range.setHorizontalAlignment("center");
  range.setFontFamily("Roboto Mono");
  range.setFontSize(10);
  
  // Bold the direction cell
  sheet.getRange(rowNum, 3).setFontWeight("bold");
}

function handleClosed(sheet, data) {
  // Find the last row that has "ACTIVE" in column L (Result) matching this symbol/direction
  var lastRow = sheet.getLastRow();
  var targetRow = -1;
  
  // Search from bottom up to find the most recent ACTIVE trade
  for (var i = lastRow; i >= 2; i--) {
    var resultCell = sheet.getRange(i, 12).getValue();
    var symbolCell = sheet.getRange(i, 2).getValue();
    if (resultCell === "ACTIVE" && symbolCell === (data.symbol || "ETH/USDT")) {
      targetRow = i;
      break;
    }
  }
  
  if (targetRow === -1) {
    // No matching OPENED row found — create a standalone closed row as fallback
    var tradeNum = lastRow;
    var fallbackRow = [
      tradeNum,
      data.symbol || "ETH/USDT",
      data.direction || "",
      data.entry_price || "",
      data.sl_price || "",
      data.tp_price || "",
      "—",
      data.exit_price || "",
      data.close_timestamp || "",
      data.duration || "N/A",
      data.candle_count || 0,
      data.exit_reason || "?",
      (data.return_pct >= 0 ? "+" : "") + parseFloat(data.return_pct || 0).toFixed(2) + "%",
      "$" + parseFloat(data.current_balance || 0).toFixed(2)
    ];
    sheet.appendRow(fallbackRow);
    targetRow = sheet.getLastRow();
  } else {
    // Update the existing OPENED row with closing details
    sheet.getRange(targetRow, 8).setValue(data.exit_price || "");                       // Exit Price
    sheet.getRange(targetRow, 9).setValue(data.close_timestamp || "");                  // Close Time
    sheet.getRange(targetRow, 10).setValue(data.duration || "N/A");                     // Duration
    sheet.getRange(targetRow, 11).setValue(data.candle_count || 0);                     // Candles
    sheet.getRange(targetRow, 12).setValue(data.exit_reason || "?");                    // Result
    var returnStr = (data.return_pct >= 0 ? "+" : "") + parseFloat(data.return_pct || 0).toFixed(2) + "%";
    sheet.getRange(targetRow, 13).setValue(returnStr);                                  // Return %
    sheet.getRange(targetRow, 14).setValue("$" + parseFloat(data.current_balance || 0).toFixed(2)); // Balance
  }
  
  // Color the row based on result
  var range = sheet.getRange(targetRow, 1, 1, 14);
  var reason = (data.exit_reason || "").toUpperCase();
  
  if (reason === "TP") {
    range.setBackground("#e8f5e9");     // Light green
    range.setFontColor("#1b5e20");      // Dark green text
  } else if (reason === "SL") {
    range.setBackground("#ffebee");     // Light red
    range.setFontColor("#b71c1c");      // Dark red text
  } else {
    range.setBackground("#f5f5f5");     // Neutral gray
    range.setFontColor("#333333");
  }
  
  // Bold the result and return cells
  sheet.getRange(targetRow, 12).setFontWeight("bold");
  sheet.getRange(targetRow, 13).setFontWeight("bold");
}
