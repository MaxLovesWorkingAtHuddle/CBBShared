fetch("https://app.opticodds.com/api/backend/screen/data?sport=basketball&league=ncaab&market=total_points&tz=America%2FLos_Angeles", { 
    headers: { "accept": "application/json" } 
})
.then(res => res.json())
.then(data => {
    const results = {};

    // 1. Create a map of column indexes to Sportsbook IDs
    // The 'columns' array in the JSON defines what each index in the 'c' array represents.
    // We use the 'sb' (sportsbook) field as the key, matching your 'col-id' logic.
    const columnMap = {};
    if (data.columns) {
        data.columns.forEach((col, index) => {
            if (col.sb) {
                columnMap[index] = col.sb;
            }
        });
    }

    // 2. Iterate through the rows
    // 'data.rows' contains the actual line data for each game/outcome.
    if (data.rows) {
        data.rows.forEach(row => {
            // The unique identifier for the row (e.g., "26124..._default_0")
            const rowId = row.i;
            
            // This object will hold all sportsbook data for this specific row
            const rowData = {};

            // 'row.c' contains the cell data. It matches the order of 'data.columns'.
            row.c.forEach((cell, index) => {
                // Skip if the cell is null (no line available for this book)
                if (!cell) return;

                const sportsbookId = columnMap[index];
                if (!sportsbookId) return;

                // Extract Line ("ln") and Price ("pr")
                // The JSON structure is usually: { "ln": { "v": 145.5 }, "pr": { "v": -110 }, "l": "o" }
                // "l" indicates label: "o" = Over, "u" = Under.
                
                const spread = cell.ln ? cell.ln.v.toString() : '';
                const price = cell.pr ? cell.pr.v.toString() : '';
                const label = cell.l; 

                // Determine outcome info based on the 'l' field or row context
                // In your previous scrape, you differentiated Over vs Under.
                // In this JSON, rows are often separated by outcome (e.g., row _0 is Away/Over, row _1 is Home/Under),
                // but individual cells also carry the "l" tag.
                
                let marketType = '';
                let outcomeIndex = 0;

                if (label === 'o') {
                    marketType = 'Over_Price';
                    outcomeIndex = 0;
                } else if (label === 'u') {
                    marketType = 'Under_Price';
                    outcomeIndex = 1;
                }

                // Construct the data object for this cell
                // Note: The previous scrape returned an array for a cell (likely allowing for multiple lines).
                // We keep that structure here.
                const cellData = [{
                    bookmaker_source: sportsbookId,
                    market_type: marketType,
                    spread: spread,
                    probability: price,
                    outcome_index: outcomeIndex
                }];

                // Assign to the sportsbook ID key
                rowData[sportsbookId] = cellData;
            });

            // Assign the processed row data to the result object
            results[rowId] = rowData;
        });
    }

    console.log(results);
    return results;
});