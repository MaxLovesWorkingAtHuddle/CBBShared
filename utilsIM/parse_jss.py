# Updated parse_jss.py

# Keep the HOS Query
HOS_GRAPHQL_QUERY = """query multiviewEvents($condition: EventCondition, $filter: EventFilter, $orderBy: [EventsOrderBy!] = [STARTS_AT_ASC]) {
  events: allEvents(filter: $filter, condition: $condition, orderBy: $orderBy) {
    nodes {
      eventId
      eventName
      startsAt
      status
      matchState
      sportId
      competitors
      isUsaView
      eventType
      source
      limbo
      sport {
        sportId
        sportName
        sportLabel
        __typename
      }
      competition {
        competitionId
        competitionName
        competitionFeedConfiguration: competitionFeedConfigurationsByCompetitionId {
          nodes {
            feed
            priority
            __typename
          }
          __typename
        }
        __typename
      }
      operatorEventSuspensionsByEventId {
        nodes {
          operatorId
          __typename
        }
        __typename
      }
      region {
        regionId
        regionName
        __typename
      }
      limitConfiguration: eventAppliedLimitConfigurationsByEventId {
        nodes {
          limitConfiguration
          __typename
        }
        __typename
      }
      markets: marketsByEventId(
        filter: {source: {in: ["INTERNAL_AGGREGATION"]}, marketCode: {in: ["POINT_HANDICAP", "GAME_HANDICAP", "POINT_OVER_UNDER", "GAME_OVER_UNDER", "RESULT"]}}
      ) {
        nodes {
          displayStatus
          offeringStatus
          resultingStatus
          marketCode
          marketId
          marketType
          selections
          source
          inPlay
          marketSummary
          limitConfiguration
          gateway
          suspensionReason
          __typename
        }
        __typename
      }
      primaryFeedOverrides: eventPrimaryFeedOverridesByEventId {
        nodes {
          primaryFeeds
          __typename
        }
        __typename
      }
      basketballEventDetails: basketballAggregatesByEventId {
        nodes {
          homeTeamId
          awayTeamId
          homeScore
          awayScore
          eventId
          nodeId
          periodLengthInMinutes
          periods
          secondsLeftInPeriod
          teamInPossession
          lastTeamToScore
          competitionType
          period
          clockRunning
          source
          homeLineup
          awayLineup
          actions
          riskFlags
          __typename
        }
        __typename
      }
      operatorEventUndisplaysByEventId {
        nodes {
          eventId
          __typename
        }
        __typename
      }
      __typename
    }
    __typename
  }
}"""

# JavaScript to extract team names (DOM Scraper - Assumes rows are still rendered)
EXTRACT_TEAM_NAMES_JS = """
// This assumes 'data' is the JSON response from the OpticOdds API
const transformApiResponse = (data, gameIds) => {
    const results = {};
    const fixtures = data.fixtures || {};

    gameIds.forEach(gameId => {
        const fixture = fixtures[gameId];
        
        if (fixture) {
            // In the JSON, home_team_display and away_team_display are standard
            const team1 = fixture.away_team_display || (fixture.away_team[0] && fixture.away_team[0].name) || '';
            const team2 = fixture.home_team_display || (fixture.home_team[0] && fixture.home_team[0].name) || '';
            
            results[gameId] = {
                team1: team1,
                team2: team2,
                display: `${team1} vs ${team2}`
            };
        } else {
            // Handle case where gameId is not found in the API response
            results[gameId] = { team1: '', team2: '', display: `Game ID: ${gameId}` };
        }
    });

    return results;
};

// Usage within your fetch call:
fetch("https://app.opticodds.com/api/backend/screen/data?sport=basketball&league=ncaab&market=main_line&tz=America%2FLos_Angeles", { 
    headers: { "accept": "application/json" } 
})
.then(res => res.json())
.then(data => {
    // Replace with your actual array of IDs you are looking for
    const myGameIds = ["21184-10896-2026-02-01", "52310-36434-2026-02-01"]; 
    const finalResults = transformApiResponse(data, myGameIds);
    console.log(finalResults);
});
"""
# parse_js.py

# -----------------------------------------------------------------------------
# 1. MONEYLINE EXTRACTION
# -----------------------------------------------------------------------------
EXTRACT_MONEYLINE_JS = """
(async () => {
    // Helper: Calculate Implied Probability (returns string "52.4")
    const calculateProbability = (americanOdds) => {
        const odds = parseFloat(americanOdds);
        if (isNaN(odds)) return "0.0";
        let prob;
        if (odds > 0) {
            prob = 100 / (odds + 100);
        } else {
            prob = Math.abs(odds) / (Math.abs(odds) + 100);
        }
        // Scale to 0-100 and fix to 1 decimal place as a string
        return (prob * 100).toFixed(1);
    };

    const transformResponse = (apiResponse) => {
        const results = {};
        const rows = apiResponse.rows;
        const columns = apiResponse.columns;

        rows.forEach((row) => {
            // Clean ID
            const rawId = row.g || "";
            const fixtureId = rawId.replace(/^fixture_/, "").replace(/_default$/, "");
            
            const outcomes = row.c; 

            if (!results[fixtureId]) {
                results[fixtureId] = {};
            }

            outcomes.forEach((outcome, colIndex) => {
                if (!outcome || !outcome.pr) return;

                const colInfo = columns[colIndex];
                const sportsbookName = colInfo.sn || colInfo.sb;

                if (!results[fixtureId][sportsbookName]) {
                    results[fixtureId][sportsbookName] = [];
                }

                // 0 = Away (Moneyline_1), 1 = Home (Moneyline_2)
                const outcomeIndex = row.p; 
                const marketType = (outcomeIndex === 0) ? "Moneyline_1" : "Moneyline_2";

                results[fixtureId][sportsbookName].push({
                    bookmaker_source: sportsbookName,
                    market_type: marketType,
                    spread: "",
                    probability: calculateProbability(outcome.pr.v), 
                    outcome_index: outcomeIndex
                });
            });
        });
        return results;
    };

    try {
        const response = await fetch("https://app.opticodds.com/api/backend/screen/data?sport=basketball&league=ncaab&market=moneyline&tz=America%2FLos_Angeles", { 
            headers: { "accept": "application/json" } 
        });
        const data = await response.json();
        return transformResponse(data);
    } catch (e) {
        return { error: e.toString() };
    }
})()
"""

# -----------------------------------------------------------------------------
# 2. SPREAD EXTRACTION
# -----------------------------------------------------------------------------
EXTRACT_SPREAD_JS = """
(async () => {
    // Helper: Calculate Implied Probability (returns string "52.4")
    const calculateProbability = (americanOdds) => {
        const odds = parseFloat(americanOdds);
        if (isNaN(odds)) return "0.0";
        let prob;
        if (odds > 0) {
            prob = 100 / (odds + 100);
        } else {
            prob = Math.abs(odds) / (Math.abs(odds) + 100);
        }
        return (prob * 100).toFixed(1);
    };

    const processBothSides = (apiData) => {
        const games = {};
        const rows = apiData.rows;
        const columns = apiData.columns;

        rows.forEach(row => {
            // Clean ID
            const rawId = row.gm || ""; 
            const gameId = rawId.replace(/^fixture_/, "").replace(/_default$/, "");

            const teamType = row.t; // "away" or "home"
            const outcomeIndex = (teamType === "away") ? 0 : 1;
            
            if (!games[gameId]) games[gameId] = {};

            columns.forEach((col, index) => {
                const cell = row.c[index];

                if (cell && cell.ln && cell.pr) {
                    const sportsbookName = col.sn || col.sb;

                    if (!games[gameId][sportsbookName]) {
                        games[gameId][sportsbookName] = [];
                    }

                    // Format Spread: Add '+' if positive, otherwise keep existing (which usually has '-')
                    let rawLine = parseFloat(cell.ln.v);
                    let formattedSpread = rawLine > 0 ? "+" + rawLine : rawLine.toString();

                    games[gameId][sportsbookName].push({
                        bookmaker_source: sportsbookName,
                        market_type: "Spread_1", 
                        spread: formattedSpread,
                        probability: calculateProbability(cell.pr.v),
                        outcome_index: outcomeIndex
                    });
                }
            });
        });
        return games;
    };

    try {
        const response = await fetch("https://app.opticodds.com/api/backend/screen/data?sport=basketball&league=ncaab&market=point_spread&tz=America%2FLos_Angeles", { 
            headers: { "accept": "application/json" } 
        });
        const data = await response.json();
        return processBothSides(data);
    } catch (e) {
        return { error: e.toString() };
    }
})()
"""
# -----------------------------------------------------------------------------
# 3. TOTALS EXTRACTION
# -----------------------------------------------------------------------------
EXTRACT_TOTALS_JS = """(async () => {
    // Helper: Calculate Implied Probability (returns string with % "55.0%")
    const calculateProbability = (americanOdds) => {
        const odds = parseFloat(americanOdds);
        if (isNaN(odds)) return "0.0%";
        let prob;
        if (odds > 0) {
            prob = 100 / (odds + 100);
        } else {
            prob = Math.abs(odds) / (Math.abs(odds) + 100);
        }
        return (prob * 100).toFixed(1) + "%";
    };

    try {
        const response = await fetch("https://app.opticodds.com/api/backend/screen/data?sport=basketball&league=ncaab&market=total_points&tz=America%2FLos_Angeles", { 
            headers: { "accept": "application/json" } 
        });
        const data = await response.json();
        const results = {};

        const columnMap = {};
        if (data.columns) {
            data.columns.forEach((col, index) => {
                if (col.sb) columnMap[index] = col.sn || col.sb;
            });
        }

        if (data.rows) {
            data.rows.forEach(row => {
                // Clean ID
                const rawId = row.i || row.gm || "";
                const rowId = rawId.replace(/^fixture_/, "").replace(/_default_1$/, "").replace(/_default_0$/, "");
                
                if (!results[rowId]) {
                    results[rowId] = {};
                }

                row.c.forEach((cell, index) => {
                    if (!cell) return;
                    const sportsbookName = columnMap[index];
                    if (!sportsbookName) return;

                    const label = cell.l || ""; // 'o' or 'u'
                    // Format Spread: prefix with o/u (e.g. "o146.5")
                    const spread = cell.ln ? (label + cell.ln.v) : '';
                    
                    let marketType = '';
                    let outcomeIndex = 0;

                    if (label === 'o') {
                        marketType = 'Over_Price';
                        outcomeIndex = 0;
                    } else if (label === 'u') {
                        marketType = 'Under_Price';
                        outcomeIndex = 1;
                    }

                    if (!results[rowId][sportsbookName]) {
                        results[rowId][sportsbookName] = [];
                    }

                    results[rowId][sportsbookName].push({
                        bookmaker_source: sportsbookName,
                        market_type: marketType,
                        spread: spread,
                        probability: calculateProbability(cell.pr.v),
                        outcome_index: outcomeIndex
                    });
                });
            });
        }
        return results;
    } catch (e) {
        return { error: e.toString() };
    }
})()"""