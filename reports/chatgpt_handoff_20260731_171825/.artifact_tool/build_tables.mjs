import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const reportDir = "C:\\robotics_sim\\wlr_robot\\resume_validation_fsm_residual_ppo\\reports\\chatgpt_handoff_20260731_171825";
const source = JSON.parse(await fs.readFile(path.join(reportDir, "_tables.json"), "utf8"));
const previewDir = path.join(reportDir, ".artifact_tool", "previews");
await fs.mkdir(previewDir, { recursive: true });

function normalize(value) {
  if (value === null || value === undefined) return "";
  if (typeof value === "object") return JSON.stringify(value);
  return value;
}

function csvCell(value) {
  const text = String(normalize(value));
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function matrixFor(rows) {
  if (!rows.length) return [["status"], ["NO_ROWS"]];
  const headers = [];
  const seen = new Set();
  for (const row of rows) {
    for (const key of Object.keys(row)) {
      if (!seen.has(key)) {
        seen.add(key);
        headers.push(key);
      }
    }
  }
  return [headers, ...rows.map((row) => headers.map((key) => normalize(row[key])))];
}

function columnName(index) {
  let n = index + 1;
  let result = "";
  while (n > 0) {
    const remainder = (n - 1) % 26;
    result = String.fromCharCode(65 + remainder) + result;
    n = Math.floor((n - 1) / 26);
  }
  return result;
}

function safeSheetName(filename, used) {
  const preferred = filename.replace(/\.csv$/i, "").replace(/[\\/?*\[\]:]/g, "_");
  let name = preferred.slice(0, 31);
  let suffix = 2;
  while (used.has(name)) {
    const tail = `_${suffix++}`;
    name = preferred.slice(0, 31 - tail.length) + tail;
  }
  used.add(name);
  return name;
}

const workbook = Workbook.create();
const usedNames = new Set();
const verification = [];

for (const [filename, rows] of Object.entries(source)) {
  const matrix = matrixFor(rows);
  const csvText = matrix.map((row) => row.map(csvCell).join(",")).join("\r\n") + "\r\n";
  await fs.writeFile(path.join(reportDir, filename), csvText, "utf8");

  // Parse every authored CSV through artifact-tool as a structural validation.
  const parsed = await Workbook.fromCSV(csvText, { sheetName: "Validated" });
  const parsedCheck = await parsed.inspect({
    kind: "table",
    range: `Validated!A1:${columnName(Math.min(matrix[0].length, 12) - 1)}${Math.min(matrix.length, 8)}`,
    include: "values,formulas",
    tableMaxRows: 8,
    tableMaxCols: 12,
    maxChars: 1800,
  });

  const sheetName = safeSheetName(filename, usedNames);
  const sheet = workbook.worksheets.add(sheetName);
  const lastColumn = columnName(matrix[0].length - 1);
  const fullRange = sheet.getRange(`A1:${lastColumn}${matrix.length}`);
  fullRange.values = matrix;
  sheet.showGridLines = false;
  sheet.freezePanes.freezeRows(1);
  sheet.getRange(`A1:${lastColumn}1`).format = {
    fill: "#17365D",
    font: { bold: true, color: "#FFFFFF" },
    wrapText: true,
    verticalAlignment: "center",
  };
  sheet.getRange(`A1:${lastColumn}${matrix.length}`).format = {
    wrapText: true,
    verticalAlignment: "top",
  };
  sheet.getRange(`A1:${lastColumn}${matrix.length}`).format.columnWidth = 22;
  sheet.getRange(`A1:${lastColumn}1`).format.rowHeight = 32;
  if (matrix.length > 1) {
    sheet.getRange(`A2:${lastColumn}${matrix.length}`).format.borders = {
      insideHorizontal: { style: "thin", color: "#D9E2F3" },
    };
  }
  const previewRange = `A1:${columnName(Math.min(matrix[0].length, 12) - 1)}${Math.min(matrix.length, 20)}`;
  const preview = await workbook.render({ sheetName, range: previewRange, scale: 1, format: "png" });
  await fs.writeFile(
    path.join(previewDir, `${sheetName}.png`),
    new Uint8Array(await preview.arrayBuffer()),
  );
  verification.push({
    file: filename,
    rows: matrix.length - 1,
    columns: matrix[0].length,
    sheet: sheetName,
    parsedPreview: parsedCheck.ndjson.slice(0, 1800),
  });
}

const workbookCheck = await workbook.inspect({
  kind: "workbook,sheet",
  include: "id,name",
  maxChars: 6000,
});
const formulaErrors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: "final formula error scan",
  maxChars: 3000,
});

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(path.join(reportDir, "AUDIT_TABLES.xlsx"));
await fs.writeFile(
  path.join(reportDir, ".artifact_tool", "artifact_verification.json"),
  JSON.stringify(
    {
      generatedAt: new Date().toISOString(),
      tables: verification,
      workbook: workbookCheck.ndjson,
      formulaErrors: formulaErrors.ndjson,
    },
    null,
    2,
  ) + "\n",
  "utf8",
);

process.stdout.write(JSON.stringify({ csvFiles: Object.keys(source).length, workbook: "AUDIT_TABLES.xlsx" }));
