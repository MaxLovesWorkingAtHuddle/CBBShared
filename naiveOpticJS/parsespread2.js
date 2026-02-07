/**
 * Processes the API response to group both Away and Home spreads by Game ID
 */
function processBothSides(apiData) {
    const results = {};
    const rows = apiData.rows;
    const columns = apiData.columns;

    // Use a temporary map to group team rows by their common Game ID (gm)
    const games = {};

    rows.forEach(row => {
        const gameId = row.gm; // The base ID shared by both teams
        const teamType = row.t; // "away" or "home"
        
        if (!games[gameId]) games[gameId] = { away: {}, home: {} };

        // Process each sportsbook column for this specific team
        columns.forEach((col, index) => {
            const colId = col.i; 
            const cell = row.c[index];

            if (cell && cell.ln && cell.pr) {
                // Determine if this is Spread_1 (Away) or Spread_2 (Home) based on team type
                const marketType = (teamType === "away") ? "Spread_1" : "Spread_2";

                games[gameId][teamType][colId] = [{
                    bookmaker_source: col.sb,
                    market_type: marketType,
                    spread: cell.ln.v.toString(),
                    probability: cell.pr.v.toString(),
                    outcome_index: (teamType === "away") ? 0 : 1
                }];
            }
        });
    });

    return games;
}

// Usage with the fetch call
fetch("https://app.opticodds.com/api/backend/screen/data?sport=basketball&league=ncaab&market=point_spread&tz=America%2FLos_Angeles", { 
    headers: { "accept": "application/json" } 
})
.then(res => res.json())
.then(data => {
    const groupedData = processBothSides(data);
    console.log(groupedData);
});