/**
 * Processes the JSON response into the required object structure
 */
function processApiData(apiData) {
    const results = {};
    const rows = apiData.rows; // Contains game and team data
    const columns = apiData.columns; // Contains sportsbook metadata

    rows.forEach(row => {
        const rowId = row.i; // Unique ID for team row [cite: 7]
        const rowData = {};

        // Iterate through columns to map them to the cell indices in row.c
        columns.forEach((col, index) => {
            const colId = col.i; // e.g., "draftkings:point_spread" 
            const cell = row.c[index];

            // Only proceed if there is spread and price data in this cell
            if (cell && cell.ln && cell.pr) {
                rowData[colId] = [{
                    bookmaker_source: col.sb, // The sportsbook identifier 
                    market_type: "Spread_1",
                    spread: cell.ln.v.toString(), // The spread value 
                    probability: cell.pr.v.toString(), // The odds price 
                    outcome_index: 0
                }];
            }
        });

        // Add to final results if the row has any sportsbook data
        if (Object.keys(rowData).length > 0) {
            results[rowId] = rowData;
        }
    });

    return results;
}

// How to use it with your fetch call
fetch("https://app.opticodds.com/api/backend/screen/data?sport=basketball&league=ncaab&market=point_spread&tz=America%2FLos_Angeles", { 
    headers: { "accept": "application/json" } 
})
.then(res => res.json())
.then(data => {
    const finalObject = processApiData(data);
    console.log(finalObject);
})
.catch(err => console.error("Error fetching or processing data:", err));