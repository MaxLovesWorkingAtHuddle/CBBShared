graphql_query = """query multiviewEvents($condition: EventCondition, $filter: EventFilter, $orderBy: [EventsOrderBy!] = [STARTS_AT_ASC]) {
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
            filter: {source: {in: ["INTERNAL_AGGREGATION"]}, marketCode: {in: ["GOAL_OVER_UNDER", "POINT_HANDICAP", "RUN_HANDICAP", "GAME_HANDICAP", "GOAL_HANDICAP", "POINT_OVER_UNDER", "RUN_OVER_UNDER", "GAME_OVER_UNDER", "RESULT"]}}
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
          soccerEventDetails: soccerAggregatesByEventId {
            nodes {
              actions
              attacksInMatch
              attacksPerPeriod
              available
              awayLineup
              awayScore
              awayScoreFirstLeg
              awayScorePenaltyShootout
              awayScoreRegularTime
              awayTeamId
              competitionType
              cornersInMatch
              cornersPerPeriod
              dangerousAttacksInMatch
              dangerousAttacksPerPeriod
              dangerousFreeKicksInMatch
              dangerousFreeKicksPerPeriod
              elapsedSecondInPeriod
              eventId
              eventInBreak
              eventPreMatch
              extraTimeHalfDuration
              extraTimePossible
              firstYellowCardsInMatch
              firstYellowCardsPerPeriod
              foulsInMatch
              foulsPerPeriod
              freeKicksInMatch
              freeKicksPerPeriod
              goStraightToPenalties
              goalKicksInMatch
              goalKicksPerPeriod
              halfDuration
              homeLineup
              homeScore
              homeScoreFirstLeg
              homeScorePenaltyShootout
              homeScoreRegularTime
              homeTeamId
              injuryTimeDuration
              injuryTimeDurationOfficial
              lastAction
              maxSubstitutions
              penaltiesInMatch
              penaltiesPerPeriod
              penaltiesPossible
              period
              redCardsInMatch
              redCardsPerPeriod
              riskFlags
              scorePerPeriod
              secondLeg
              shotsOffTargetInMatch
              shotsOffTargetPerPeriod
              shotsOnTargetInMatch
              shotsOnTargetPerPeriod
              source
              substitutionsInMatch
              substitutionsPerPeriod
              teamInPossession
              throwInsInMatch
              throwInsPerPeriod
              var
              varEnabled
              yellowCardsInMatch
              yellowCardsPerPeriod
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
              foulThresholdForBonus
              foulsPerPeriod
              eventId
              ftsToCome
              nodeId
              onePointersPerPeriod
              otLengthInMinutes
              otPossible
              periodLengthInMinutes
              periods
              scorePerPeriod
              secondsLeftInPeriod
              teamInPossession
              threePointersPerPeriod
              twoPointersPerPeriod
              lastTeamToScore
              competitionType
              period
              clockRunning
              source
              homeLineup
              awayLineup
              fieldGoalPerPeriod
              fieldGoalPercentagePerPeriod
              fieldGoalPercentageInMatch
              twoPointAttemptsPerPeriod
              threePointAttemptsPerPeriod
              reboundsPerPeriod
              assistsPerPeriod
              possessionsCountPerPeriod
              eventInBreak
              eventPreMatch
              actions
              stealsPerPeriod
              turnoversPerPeriod
              offensiveReboundsPerPeriod
              blocksPerPeriod
              riskFlags
              __typename
            }
            __typename
          }
          footballEventDetails: footballAggregatesByEventId {
            nodes {
              period
              gameTimeFromLastScoringEvent
              gameTimeElapsedInPeriod
              gameTimeRemainingInRegularGame
              inPossession
              downNumber
              yardsToWinDown
              lineOfScrimmageYard
              lineOfScrimmageTerritory
              yardsToEndZone
              isConversionEvent
              homeScore
              awayScore
              homeScoreFirstQuarter
              awayScoreFirstQuarter
              homeScoreSecondQuarter
              awayScoreSecondQuarter
              homeScoreThirdQuarter
              awayScoreThirdQuarter
              homeScoreFourthQuarter
              awayScoreFourthQuarter
              homeScoreOvertime
              awayScoreOvertime
              competitionName
              totalDownsNumber
              quarterDuration
              overtimeDuration
              overtimePossible
              homeTeamId
              awayTeamId
              source
              homeLineup
              awayLineup
              drives
              eventInBreak
              eventPreMatch
              isPlayRunning: playRunning
              riskFlags
              __typename
            }
            __typename
          }
          ultimateEventDetails: ultimateAggregatesByEventId {
            nodes {
              homeTeamId
              awayTeamId
              homeScore
              awayScore
              eventId
              nodeId
              available
              clockRunning
              lastTeamToScore
              lastUpdated
              numberOfPeriods
              overTimeLengthMinutes
              period
              periodLengthMinutes
              pitchLengthMeters
              pitchWidthMeters
              scorePerPeriod
              secondsLeftInPeriod
              source
              teamInPossession
              eventInBreak
              eventPreMatch
              __typename
            }
            __typename
          }
          hockeyEventDetails: hockeyAggregatesByEventId {
            nodes {
              eventId
              lastTeamToScore
              period
              secondsLeftInPeriod
              scorePerPeriod
              foulsPerPeriod: penaltiesPerPeriod
              periods
              periodLengthInMinutes
              competitionType
              otPossible
              otLengthInMinutes
              homeTeamId
              awayTeamId
              homeScore
              awayScore
              clockRunning
              timeOfLastClockStart
              lastUpdated
              source
              available
              teamInPossession
              eventInBreak
              eventPreMatch
              riskFlags
              powerPlayAdvantage
              __typename
            }
            __typename
          }
          baseballEventDetails: baseballAggregatesByEventId {
            nodes {
              eventId
              source
              lastUpdated
              matchRuns
              pitchCount
              loadedBases
              matchHits
              inningDetails
              currentTeamAPitcherProviderId
              currentTeamABatterProviderId
              currentTeamAPitcherId
              currentTeamABatterId
              currentTeamBPitcherProviderId
              currentTeamBBatterProviderId
              currentTeamBPitcherId
              currentTeamBBatterId
              teamABatterIds
              teamBBatterIds
              teamAPitcherIds
              teamBPitcherIds
              matchHomeRuns
              raceToMap
              available
              extraInningsSecondBaseRule
              regularInningsToBePlayed
              mercyRulePossible
              mercyRuleInningThreshold
              mercyRuleRunsAheadThreshold
              tiePossible
              tiePossibleInningThreshold
              homeTeamId
              awayTeamId
              eventInBreak
              eventPreMatch
              riskFlags
              __typename
            }
            __typename
          }
          tennisEventDetails: tennisAggregatesByEventId {
            nodes {
              source
              lastUpdated
              homeTeamId
              awayTeamId
              available
              period
              matchTime
              setDurations
              currentServingTeam
              currentGameNumber
              currentGameScore
              pointsWonPerGame
              gamesWonInMatch
              gamesWonPerSet
              setsWon
              isPointInProgress
              secondServe
              eventPrematch
              eventPostmatch
              eventInBreak
              setsToPlay
              isDoubles
              isMen
              noAdvantage
              lastSetSuperTiebreak
              lastScoreUpdate
              lastSetSuperTiebreakPoints
              acesInMatch
              acesPerSet
              doubleFaultsInMatch
              doubleFaultsPerSet
              breakPointsPlayedInMatch
              breakPointsWonInMatch
              breakPointsPlayedPerSet
              breakPointsWonPerSet
              breakPointsWonPercentageInMatch
              breakServePointsWonPercentagePerSet
              firstServePercentageInMatch
              firstServePercentagePerSet
              firstServePointsPlayedInMatch
              firstServePointsPlayedPerSet
              firstServePointsWonInMatch
              firstServePointsWonPerSet
              firstServePointsWonPercentageInMatch
              firstServePointsWonPercentagePerSet
              secondServePercentageInMatch
              secondServePercentagePerSet
              secondServePointsPlayedInMatch
              secondServePointsPlayedPerSet
              secondServePointsWonInMatch
              secondServePointsWonPerSet
              secondServePointsWonPercentageInMatch
              secondServePointsWonPercentagePerSet
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
graphql_query = """query multiviewEvents($condition: EventCondition, $filter: EventFilter, $orderBy: [EventsOrderBy!] = [STARTS_AT_ASC]) {
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
EXTRACT_TOTALS_JS = """
() => {
    const rows = document.querySelectorAll('.ag-center-cols-container [role="row"][row-index]');
    const results = {};
    
    rows.forEach(row => {
        const rowId = row.getAttribute('row-id');
        if (!rowId) return;
        
        const cells = row.querySelectorAll('[role="gridcell"][col-id]');
        const rowData = {};
        
        cells.forEach(cell => {
            const colId = cell.getAttribute('col-id');
            if (!colId) return;
            
            const dataRows = cell.querySelectorAll('div.box-border.flex.w-full.cursor-pointer.flex-col.justify-center');
            const columnData = [];
            
            // Process first row (Over/Under - OVER side)
            if (dataRows[0]) {
                const spread = dataRows[0].querySelector('div.font-bold.tracking-tighter')?.textContent?.split('/')[0]?.split('\\n')?.pop()?.trim() || '';
                let probability = '';
                
                if (colId === 'Pinnacle') {
                    probability = dataRows[0].querySelector('span.text-\\\\[13px\\\\]')?.textContent?.trim() || '';
                } else if (colId === 'bestPrice') {
                    probability = dataRows[0].querySelector('div.mr-1.font-medium')?.textContent?.replace('/', '')?.trim() || '';
                } else {
                    probability = dataRows[0].querySelector('div.text-sm.text-brand-gray-7')?.textContent?.trim() || '';
                }
                
                let source = colId;
                if (colId === 'bestPrice') {
                    const img = dataRows[0].querySelector('img.remix-image');
                    source = img?.getAttribute('alt') || colId;
                }
                
                columnData.push({
                    bookmaker_source: source,
                    market_type: 'Over_Price',
                    spread: spread,
                    probability: probability,
                    outcome_index: 0
                });
            }
            
            // Process second row (Under)
            if (dataRows[1]) {
                const spread = dataRows[1].querySelector('div.font-bold.tracking-tighter')?.textContent?.split('/')[0]?.split('\\n')?.pop()?.trim() || '';
                let probability = '';
                
                if (colId === 'Pinnacle') {
                    probability = dataRows[1].querySelector('span.text-\\\\[13px\\\\]')?.textContent?.trim() || '';
                } else {
                    probability = dataRows[1].querySelector('div.text-sm.text-brand-gray-7')?.textContent?.trim() || '';
                }
                
                let source = colId;
                if (colId === 'bestPrice') {
                    const img = dataRows[1].querySelector('img.remix-image');
                    source = img?.getAttribute('alt') || colId;
                }
                
                if (probability) {
                    columnData.push({
                        bookmaker_source: source,
                        market_type: 'Under_Price',
                        spread: spread,
                        probability: probability,
                        outcome_index: 1
                    });
                }
            }
            
            rowData[colId] = columnData;
        });
        
        results[rowId] = rowData;
    });
    
    return results;
}
"""
EXTRACT_MONEYLINE_JS = """
() => {
    const rows = document.querySelectorAll('.ag-center-cols-container [role="row"][row-index]');
    const results = {};
    
    rows.forEach(row => {
        const rowId = row.getAttribute('row-id');
        if (!rowId) return;
        
        const cells = row.querySelectorAll('[role="gridcell"][col-id]');
        const rowData = {};
        
        cells.forEach(cell => {
            const colId = cell.getAttribute('col-id');
            if (!colId) return;

            // Skip info columns
            if (['startTime', 'rotationNumber', 'teamName'].includes(colId)) return;
            
            const oddsBoxes = cell.querySelectorAll('div.cursor-pointer');
            const columnData = [];
            
            let source = colId;
            if (colId === 'bestPrice') {
                const img = cell.querySelector('img.remix-image');
                source = img?.getAttribute('alt') || colId;
            }

            oddsBoxes.forEach((box, index) => {
                const textContent = box.innerText || "";
                let probability = "";

                if (textContent.includes('%')) {
                    probability = textContent.replace('%', '').trim();
                } else {
                    probability = textContent.trim();
                }
                
                let marketType = (index === 0) ? "Moneyline_1" : "Moneyline_2";

                if (probability) {
                    columnData.push({
                        bookmaker_source: source,
                        market_type: marketType,
                        spread: "", 
                        probability: probability,
                        outcome_index: index
                    });
                }
            });
            
            if (columnData.length > 0) {
                rowData[colId] = columnData;
            }
        });
        
        if (Object.keys(rowData).length > 0) {
            results[rowId] = rowData;
        }
    });
    
    return results;
}
"""

# JavaScript for SPREAD extraction (from parse_page_spread.py)
EXTRACT_SPREAD_JS = """
() => {
    const rows = document.querySelectorAll('.ag-center-cols-container [role="row"][row-index]');
    const results = {};
    
    rows.forEach(row => {
        const rowId = row.getAttribute('row-id');
        if (!rowId) return;
        
        const cells = row.querySelectorAll('[role="gridcell"][col-id]');
        const rowData = {};
        
        cells.forEach(cell => {
            const colId = cell.getAttribute('col-id');
            if (!colId) return;

            // Skip info columns
            if (['startTime', 'rotationNumber', 'teamName'].includes(colId)) return;
            
            const oddsBoxes = cell.querySelectorAll('div.cursor-pointer');
            const columnData = [];
            
            let source = colId;
            if (colId === 'bestPrice') {
                const img = cell.querySelector('img.remix-image');
                source = img?.getAttribute('alt') || colId;
            }

            oddsBoxes.forEach((box, index) => {
                let spread = "";
                let probability = "";
                
                const fullText = box.innerText.trim();
                const parts = fullText.split(/[\\n/]/).map(s => s.trim()).filter(s => s.length > 0);
                
                if (parts.length >= 2) {
                    spread = parts[0];
                    probability = parts[1].replace('%', '').trim();
                } else if (parts.length === 1) {
                    if (parts[0].includes('%')) {
                        probability = parts[0].replace('%', '').trim();
                    } else {
                        spread = parts[0];
                    }
                }
                
                if (spread) spread = spread.replace('/', '').trim();

                let marketType = (index === 0) ? "Spread_1" : "Spread_2";

                if (probability || spread) {
                    columnData.push({
                        bookmaker_source: source,
                        market_type: marketType,
                        spread: spread, 
                        probability: probability,
                        outcome_index: index
                    });
                }
            });
            
            if (columnData.length > 0) {
                rowData[colId] = columnData;
            }
        });
        
        if (Object.keys(rowData).length > 0) {
            results[rowId] = rowData;
        }
    });
    
    return results;
}
"""

# JavaScript to extract team names
EXTRACT_TEAM_NAMES_JS = """
(gameIds) => {
    const results = {};
    gameIds.forEach(gameId => {
        try {
            const row = document.querySelector(`[row-id="${gameId}"]`);
            if (row) {
                const teamCell = row.querySelector('[col-id="teamName"]');
                const teamDivs = teamCell.querySelectorAll('.min-w-0.truncate.text-sm.font-medium');
                
                if (teamDivs.length >= 2) {
                    const team1 = teamDivs[0].textContent.trim();
                    const team2 = teamDivs[1].textContent.trim();
                    results[gameId] = {
                        team1: team1,
                        team2: team2,
                        display: `${team1} vs ${team2}`
                    };
                } else {
                    results[gameId] = { team1: '', team2: '', display: `Game ID: ${gameId}` };
                }
            } else {
                results[gameId] = { team1: '', team2: '', display: `Game ID: ${gameId}` };
            }
        } catch {
            results[gameId] = { team1: '', team2: '', display: `Game ID: ${gameId}` };
        }
    });
    return results;
}
"""


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
            filter: {source: {in: ["INTERNAL_AGGREGATION"]}, marketCode: {in: ["GOAL_OVER_UNDER", "POINT_HANDICAP", "RUN_HANDICAP", "GAME_HANDICAP", "GOAL_HANDICAP", "POINT_OVER_UNDER", "RUN_OVER_UNDER", "GAME_OVER_UNDER", "RESULT"]}}
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
          soccerEventDetails: soccerAggregatesByEventId {
            nodes {
              homeScore
              awayScore
              period
              __typename
            }
            __typename
          }
          basketballEventDetails: basketballAggregatesByEventId {
            nodes {
              homeScore
              awayScore
              period
              clockRunning
              secondsLeftInPeriod
              __typename
            }
            __typename
          }
          footballEventDetails: footballAggregatesByEventId {
            nodes {
              homeScore
              awayScore
              period
              __typename
            }
            __typename
          }
          hockeyEventDetails: hockeyAggregatesByEventId {
            nodes {
              homeScore
              awayScore
              period
              __typename
            }
            __typename
          }
          baseballEventDetails: baseballAggregatesByEventId {
            nodes {
              matchRuns
              inningDetails
              __typename
            }
            __typename
          }
          __typename
        }
        __typename
      }
    }"""
EXTRACT_MONEYLINE_JS = """// Assuming 'apiResponse' is the JSON data from your fetch call
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
});"""
EXTRACT_SPREAD_JS = """/**
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
});"""
EXTRACT_TOTALS_JS = """fetch("https://app.opticodds.com/api/backend/screen/data?sport=basketball&league=ncaab&market=total_points&tz=America%2FLos_Angeles", { 
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
});"""