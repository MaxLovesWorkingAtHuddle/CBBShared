// Assuming 'apiResponse' is the JSON data from your fetch call
const transformResponse = (apiResponse) => {
    const results = {};
    const rows = apiResponse.rows;
    const columns = apiResponse.columns;

    // We process rows in pairs (away/home) as they share the same fixture ID
    rows.forEach((row) => {
        const fixtureId = row.g; // The fixture grouping ID
        const teamName = row.n;
        const outcomes = row.c; // Array of odds corresponding to columns

        // Initialize the fixture entry if it doesn't exist
        if (!results[fixtureId]) {
            results[fixtureId] = {};
        }

        outcomes.forEach((outcome, colIndex) => {
            if (!outcome || !outcome.pr) return;

            const colInfo = columns[colIndex];
            const colId = colInfo.i; // e.g., "draftkings:moneyline"
            const sportsbookName = colInfo.sb; // e.g., "draftkings"

            // Initialize the column array for this fixture if it doesn't exist
            if (!results[fixtureId][colId]) {
                results[fixtureId][colId] = [];
            }

            // Determine if this is the first (away) or second (home) team in the pair
            // Based on your original logic: index 0 -> Moneyline_1, index 1 -> Moneyline_2
            const outcomeIndex = row.p; 
            const marketType = (outcomeIndex === 0) ? "Moneyline_1" : "Moneyline_2";

            results[fixtureId][colId].push({
                bookmaker_source: sportsbookName,
                market_type: marketType,
                spread: "",
                probability: outcome.pr.v.toString(), // The odds value
                outcome_index: outcomeIndex
            });
        });
    });

    return results;
};

// Implementation with fetch
fetch("https://app.opticodds.com/api/backend/screen/data?sport=basketball&league=ncaab&market=moneyline&tz=America%2FLos_Angeles", { 
    headers: { "accept": "application/json" } 
})
.then(res => res.json())
.then(data => {
    const formattedData = transformResponse(data);
    console.log(formattedData);
});