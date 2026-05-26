# Convert all CSV files in the current directory into Excel files
# Auto-fit header columns and add filter row

# Start Excel COM object
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

# Process each CSV
Get-ChildItem -Filter *.csv | ForEach-Object {

    $csvPath = $_.FullName
    $xlsxPath = [System.IO.Path]::ChangeExtension($csvPath, ".xlsx")

    Write-Host "Processing $($_.Name)..."

    # Open the CSV file
    $workbook = $excel.Workbooks.Open($csvPath)
    $sheet = $workbook.Worksheets.Item(1)

    # Auto-fit all columns in the used range
    $used = $sheet.UsedRange
    $used.Columns.AutoFit() | Out-Null

    # Add filter row (Excel filter on header)
    $used.AutoFilter() | Out-Null

    # Save as XLSX
    $workbook.SaveAs($xlsxPath, 51)   # 51 = xlOpenXMLWorkbook (.xlsx)

    # Close workbook
    $workbook.Close($false)
}

# Quit Excel
$excel.Quit()

Write-Host "Done."