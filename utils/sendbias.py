async def update_market_bias(page, context, event_id, market_id, value, is_main_line=True):
    """
    Sends the bias update via API Request (Bypasses CORS).
    Automatically fetches the current token from the browser page.
    
    Args:
        page: Playwright page object
        context: Playwright browser context object
        event_id: Event ID to update
        market_id: Market ID to update
        value: Bias value to apply
        is_main_line: Whether this is the main line (default True)
    """
    # print(f"--- Attempting to update bias for Market {market_id} ---")

    # Dynamically grab the token from LocalStorage to ensure it's fresh
    # Note: This script assumes standard Cognito storage. If your app uses a different key, 
    # you might need to adjust the javascript inside evaluate().
    
    token = await page.evaluate("""() => {
        // Find a key in localStorage that looks like an access token (Cognito usually)
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key.includes('accessToken') || key.includes('idToken')) {
                return localStorage.getItem(key);
            }
        }
        return null;
    }""")
    if not token:
        print("X Error: Could not find Authorization token in LocalStorage.")
        return False

    # Perform the API request using Playwright's APIRequestContext
    # This runs from Python, not the browser page, avoiding CORS completely.
    response = await context.request.post(
        f"https://c.phxp.huddle.tech/events/{event_id}/markets/{market_id}/apply-bias/propagate",
        headers={
            "accept": "*/*",
            "content-type": "application/json",
            "authorization": f"Bearer {token}",
            "x-admin-for": "Huddle"
        },
        data={
            # "value": value,
            "value": max(-0.05, min(value, 0.05)),
            "isMainLine": is_main_line
        }
    )

    if response.ok:
        # print(f"YES! Success! Status: {response.status}")
        print(await response.json())
        pass
    else:
        print(f"X Failed. Status: {response.status}. ")
        print(await response.text())
        return False
    return True


# def update_market_bias2(page, context, event_id, market_id, value, is_main_line=True):
#     print(f"--- Attempting to update bias for Market {market_id} ---")

#     # 1. Get the full storage state (Cookies + LocalStorage)
#     state = context.storage_state()
    
#     # 2. Extract the token from origin storage
#     # This filters through local storage items for keys containing 'accessToken'
#     token = None
#     for origin in state.get('origins', []):
#         for item in origin.get('localStorage', []):
#             if 'accessToken' in item['name'] or 'idToken' in item['name']:
#                 token = item['value']
#                 break
#         if token: break
#     if not token:
#         print("X Error: Could not find Authorization token in Storage State.")
#         return

#     # 3. Perform the API request
#     response = context.request.post(
#         f"https://c.phxp.huddle.tech/events/{event_id}/markets/{market_id}/apply-bias/propagate",
#         headers={
#             "accept": "*/*",
#             "content-type": "application/json",
#             "authorization": f"Bearer {token}",
#             "x-admin-for": "Huddle"
#         },
#         data={
#             "value": value,
#             "isMainLine": is_main_line
#         }
#     )

#     if response.ok:
#         print(f"YES! Success! Status: {response.status}")
#     else:
#         print(f"X Failed. Status: {response.status} - {response.text()}")

