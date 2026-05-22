/**
 * ETH Champion Bot — Institutional Grade Webhook & Ledger
 * 
 * DEPLOYMENT & SETUP:
 *   1. Paste this entire file into your Google Apps Script editor.
 *   2. Select the function 'setupInstitutionalSheet' from the top toolbar dropdown.
 *   3. Click "Run" to instantly format your spreadsheet with premium, institutional-grade headers.
 *   4. Click Deploy → New Deployment → Web App (Execute as Me, Access: Anyone).
 */

function setupInstitutionalSheet() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName("Trade Ledger");
  if (!sheet) {
    sheet = ss.insertSheet("Trade Ledger");
  }
  
  var headers = [
    "TRADE ID", "ASSET", "TYPE", "ENTRY", "STOP LOSS", "TAKE PROFIT", 
    "OPEN TIME (UTC)", "EXIT PRICE", "CLOSE TIME (UTC)", "DURATION", 
    "CANDLES", "RESULT", "NET RETURN", "RUNNING BALANCE"
  ];
  
  var headerRange = sheet.getRange(1, 1, 1, headers.length);
  headerRange.setValues([headers]);
  
  // Premium Institutional Styling
  headerRange.setBackground("#0F172A"); // Slate 900
  headerRange.setFontColor("#F8FAFC");  // Slate 50
  headerRange.setFontWeight("bold");
  headerRange.setFontFamily("Inter");
  headerRange.setFontSize(11);
  headerRange.setHorizontalAlignment("center");
  headerRange.setVerticalAlignment("middle");
  sheet.setRowHeight(1, 40);
  
  // Subtle bottom border for header
  headerRange.setBorder(null, null, true, null, null, null, "#334155", SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
  
  sheet.setFrozenRows(1);
  
  // Exact column sizing for data readability
  sheet.setColumnWidth(1, 90);   // TRADE ID
  sheet.setColumnWidth(2, 110);  // ASSET
  sheet.setColumnWidth(3, 90);   // TYPE
  sheet.setColumnWidth(4, 110);  // ENTRY
  sheet.setColumnWidth(5, 110);  // SL
  sheet.setColumnWidth(6, 110);  // TP
  sheet.setColumnWidth(7, 180);  // OPEN TIME
  sheet.setColumnWidth(8, 110);  // EXIT
  sheet.setColumnWidth(9, 180);  // CLOSE TIME
  sheet.setColumnWidth(10, 100); // DURATION
  sheet.setColumnWidth(11, 90);  // CANDLES
  sheet.setColumnWidth(12, 110); // RESULT
  sheet.setColumnWidth(13, 120); // NET RETURN
  sheet.setColumnWidth(14, 150); // BALANCE
  
  // Base formatting for data rows (JetBrains Mono for numbers)
  var fullRange = sheet.getRange(2, 1, 1000, headers.length);
  fullRange.setFontFamily("Consolas"); // Safe monospace fallback
  fullRange.setFontSize(10);
  fullRange.setHorizontalAlignment("center");
  fullRange.setVerticalAlignment("middle");
  
  // Number formatting for prices
  sheet.getRange("D2:F1000").setNumberFormat("$#,##0.00");
  sheet.getRange("H2:H1000").setNumberFormat("$#,##0.00");
  sheet.getRange("N2:N1000").setNumberFormat("$#,##0.00");
}

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
  var tradeNum = Math.max(1, sheet.getLastRow()); 
  var newRow = [
    "TRD-" + ('0000' + tradeNum).slice(-4), 
    data.symbol || "ETH/USDT",       
    data.direction || "",            
    data.entry_price || "",          
    data.sl_price || "",             
    data.tp_price || "",             
    data.open_timestamp || "",       
    "—",                             
    "—",                             
    "ACTIVE",                        
    "—",                             
    "ACTIVE",                        
    "—",                             
    data.current_balance || 0
  ];
  
  sheet.appendRow(newRow);
  
  var rowNum = sheet.getLastRow();
  var range = sheet.getRange(rowNum, 1, 1, 14);
  range.setBackground("#FFFBEB");       // Very soft amber/orange
  range.setFontColor("#451A03");        // Deep amber text
  range.setFontWeight("normal");
  
  // Highlight Direction
  sheet.getRange(rowNum, 3).setFontWeight("bold");
}

function handleClosed(sheet, data) {
  var lastRow = sheet.getLastRow();
  var targetRow = -1;
  
  for (var i = lastRow; i >= 2; i--) {
    if (sheet.getRange(i, 12).getValue() === "ACTIVE") {
      targetRow = i;
      break;
    }
  }
  
  if (targetRow === -1) {
    var tradeNum = Math.max(1, lastRow);
    var fallbackRow = [
      "TRD-" + ('0000' + tradeNum).slice(-4),
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
      data.current_balance || 0
    ];
    sheet.appendRow(fallbackRow);
    targetRow = sheet.getLastRow();
  } else {
    sheet.getRange(targetRow, 8).setValue(data.exit_price || "");
    sheet.getRange(targetRow, 9).setValue(data.close_timestamp || "");
    sheet.getRange(targetRow, 10).setValue(data.duration || "N/A");
    sheet.getRange(targetRow, 11).setValue(data.candle_count || 0);
    sheet.getRange(targetRow, 12).setValue(data.exit_reason || "?");
    var returnStr = (data.return_pct >= 0 ? "+" : "") + parseFloat(data.return_pct || 0).toFixed(2) + "%";
    sheet.getRange(targetRow, 13).setValue(returnStr);
    sheet.getRange(targetRow, 14).setValue(data.current_balance || 0);
  }
  
  var range = sheet.getRange(targetRow, 1, 1, 14);
  var reason = (data.exit_reason || "").toUpperCase();
  
  if (reason === "TP") {
    range.setBackground("#F0FDF4");     // Crisp institutional green
    range.setFontColor("#14532D");      // Dark emerald text
  } else if (reason === "SL") {
    range.setBackground("#FEF2F2");     // Crisp institutional red
    range.setFontColor("#7F1D1D");      // Dark ruby text
  }
  
  // Emphasize the result columns
  sheet.getRange(targetRow, 12).setFontWeight("bold"); // RESULT
  sheet.getRange(targetRow, 13).setFontWeight("bold"); // NET RETURN
}
