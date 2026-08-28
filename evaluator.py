import os
import json
from agent import build_agent_graph
from utils import get_gemini_client
from google.genai import types

TEST_REPO_ID = "corsairdev-corsair"

EVAL_DATASET = [
  {
    "question": "What is the name of the symbol used to store internal config in the corsair instance?",
    "ground_truth": "The symbol used is CORSAIR_INTERNAL.",
    "ground_truth_files": [
      "packages/corsair/core/index.ts"
    ],
    "ground_truth_functions": [
      "createCorsair"
    ]
  },
  {
    "question": "Which function is responsible for building the OAuth authorize URL?",
    "ground_truth": "The generateOAuthUrl function builds the OAuth authorize URL.",
    "ground_truth_files": [
      "packages/corsair/oauth/index.ts"
    ],
    "ground_truth_functions": [
      "generateOAuthUrl"
    ]
  },
  {
    "question": "What error is thrown when attempting to generate an OAuth URL for a plugin that lacks an oauthConfig?",
    "ground_truth": "An OAuthCallbackError is thrown with the code 'plugin_has_no_oauth_config'.",
    "ground_truth_files": [
      "packages/corsair/oauth/index.ts"
    ],
    "ground_truth_functions": [
      "getOAuthConfig"
    ]
  },
  {
    "question": "Does the Corsair ORM support string prefix matching in its search filters?",
    "ground_truth": "Yes, it supports prefix matching using the 'startsWith' property in the StringDataFilter.",
    "ground_truth_files": [
      "packages/corsair/db/orm.ts"
    ],
    "ground_truth_functions": [
      "buildWhere"
    ]
  },
  {
    "question": "Which utility function safely parses JSON-like values from the database in the ORM?",
    "ground_truth": "The parseJsonLike function attempts to run JSON.parse and falls back to returning the string if it fails.",
    "ground_truth_files": [
      "packages/corsair/db/orm.ts"
    ],
    "ground_truth_functions": [
      "parseJsonLike"
    ]
  },
  {
    "question": "What are the four main table clients returned by the createCorsairOrm function?",
    "ground_truth": "The four main table clients are integrations, accounts, entities, and events.",
    "ground_truth_files": [
      "packages/corsair/db/orm.ts"
    ],
    "ground_truth_functions": [
      "createCorsairOrm"
    ]
  },
  {
    "question": "What is the expected data type of the tenantId parameter in the withTenant method?",
    "ground_truth": "The tenantId parameter must be a non-empty string.",
    "ground_truth_files": [
      "packages/corsair/core/index.ts"
    ],
    "ground_truth_functions": [
      "createCorsair"
    ]
  },
  {
    "question": "Which function constructs a synthetic webhook body specifically for Google Channel events?",
    "ground_truth": "The buildGoogleChannelBody function constructs the synthetic body.",
    "ground_truth_files": [
      "packages/corsair/webhooks/index.ts"
    ],
    "ground_truth_functions": [
      "buildGoogleChannelBody"
    ]
  },
  {
    "question": "Which HTTP header is checked to determine the resource URI for a Google Channel event?",
    "ground_truth": "The 'x-goog-resource-uri' header is used to determine the resource URI.",
    "ground_truth_files": [
      "packages/corsair/webhooks/index.ts"
    ],
    "ground_truth_functions": [
      "buildGoogleChannelBody"
    ]
  },
  {
    "question": "Which SQL query builder library serves as the foundation for the Corsair ORM?",
    "ground_truth": "The ORM uses the 'kysely' library as its query builder.",
    "ground_truth_files": [
      "packages/corsair/db/orm.ts"
    ],
    "ground_truth_functions": [
      "createBaseTableClient"
    ]
  },
  {
    "question": "What transformation does the normalizeHeaders function apply to incoming HTTP header keys?",
    "ground_truth": "The normalizeHeaders function converts all header keys to lowercase.",
    "ground_truth_files": [
      "packages/corsair/webhooks/index.ts"
    ],
    "ground_truth_functions": [
      "normalizeHeaders"
    ]
  },
  {
    "question": "Which function is called during processOAuthCallback to guarantee that a tenant account record exists in the database?",
    "ground_truth": "The ensureAccount function is called to verify or create the tenant account row.",
    "ground_truth_files": [
      "packages/corsair/oauth/index.ts"
    ],
    "ground_truth_functions": [
      "ensureAccount",
      "processOAuthCallback"
    ]
  },
  {
    "question": "What function merges tokens from the OAuth provider with auxiliary callback parameters?",
    "ground_truth": "The mergeOAuthProviderData function handles merging these objects.",
    "ground_truth_files": [
      "packages/corsair/oauth/index.ts"
    ],
    "ground_truth_functions": [
      "mergeOAuthProviderData"
    ]
  },
  {
    "question": "Does the processOAuthCallback function work exclusively with multi-tenant instances?",
    "ground_truth": "No, processOAuthCallback supports both single-tenant and multi-tenant instances, as it always resolves a tenantId (defaulting to 'default' in single-tenant setups).",
    "ground_truth_files": [
      "packages/corsair/oauth/index.ts"
    ],
    "ground_truth_functions": [
      "processOAuthCallback"
    ]
  },
  {
    "question": "What is the specific TypeScript return type of the processWebhook function?",
    "ground_truth": "The processWebhook function returns a WebhookFilterResult object.",
    "ground_truth_files": [
      "packages/corsair/webhooks/index.ts"
    ],
    "ground_truth_functions": [
      "processWebhook"
    ]
  },
  {
    "question": "What exception is thrown if the withTenant method is invoked with an empty string?",
    "ground_truth": "It throws a standard Error with the message 'corsair.withTenant(tenantId): tenantId must be a non-empty string'.",
    "ground_truth_files": [
      "packages/corsair/core/index.ts"
    ],
    "ground_truth_functions": [
      "createCorsair"
    ]
  },
  {
    "question": "Which function is responsible for resolving the root permissions config during corsair initialization?",
    "ground_truth": "The resolveRootPermissionsConfig function resolves the permissions configuration.",
    "ground_truth_files": [
      "packages/corsair/core/index.ts"
    ],
    "ground_truth_functions": [
      "createCorsair"
    ]
  },
  {
    "question": "Which imported function is responsible for exchanging an authorization code for access and refresh tokens?",
    "ground_truth": "The exchangeCodeForTokens function is used to exchange the code for tokens.",
    "ground_truth_files": [
      "packages/corsair/oauth/index.ts"
    ],
    "ground_truth_functions": [
      "processOAuthCallback"
    ]
  },
  {
    "question": "In the Corsair ORM, what SQL operator does the 'endsWith' filter map to?",
    "ground_truth": "The 'endsWith' filter maps to the 'like' operator in the underlying SQL query.",
    "ground_truth_files": [
      "packages/corsair/db/orm.ts"
    ],
    "ground_truth_functions": [
      "buildWhere"
    ]
  },
  {
    "question": "What happens if a database is not configured but a method on a table client is invoked?",
    "ground_truth": "The assertDatabaseConfigured function will throw an error stating 'Corsair database is not configured'.",
    "ground_truth_files": [
      "packages/corsair/db/orm.ts"
    ],
    "ground_truth_functions": [
      "assertDatabaseConfigured",
      "createBaseTableClient"
    ]
  },
  {
    "question": "Which factory function instantiates the ORM client for the integrations table?",
    "ground_truth": "The createIntegrationsClient function instantiates the client.",
    "ground_truth_files": [
      "packages/corsair/db/orm.ts"
    ],
    "ground_truth_functions": [
      "createIntegrationsClient"
    ]
  },
  {
    "question": "Which ORM method is used specifically to list events scoped to a single account?",
    "ground_truth": "The listByAccount method on the events client is used.",
    "ground_truth_files": [
      "packages/corsair/db/orm.ts"
    ],
    "ground_truth_functions": [
      "createEventsClient"
    ]
  },
  {
    "question": "What is the exact database table name used to store integrations?",
    "ground_truth": "The table name is 'corsair_integrations'.",
    "ground_truth_files": [
      "packages/corsair/db/orm.ts"
    ],
    "ground_truth_functions": [
      "createIntegrationsClient"
    ]
  },
  {
    "question": "What is the exact database table name used to store tenant accounts?",
    "ground_truth": "The table name is 'corsair_accounts'.",
    "ground_truth_files": [
      "packages/corsair/db/orm.ts"
    ],
    "ground_truth_functions": [
      "createAccountsClient"
    ]
  },
  {
    "question": "Which function recursively traverses the webhook tree to identify a matching handler?",
    "ground_truth": "The findMatchingWebhook function recursively searches the webhook tree.",
    "ground_truth_files": [
      "packages/corsair/webhooks/index.ts"
    ],
    "ground_truth_functions": [
      "findMatchingWebhook"
    ]
  },
  {
    "question": "What property on a webhook handler's response instructs processWebhook to relay data back to the HTTP client?",
    "ground_truth": "The 'returnToSender' property on the handler's response is used.",
    "ground_truth_files": [
      "packages/corsair/webhooks/index.ts"
    ],
    "ground_truth_functions": [
      "processWebhook"
    ]
  },
  {
    "question": "How does generateOAuthUrl modify the state parameter in the URL when the hubConnect flag is set to true?",
    "ground_truth": "When hubConnect is true, the state parameter is explicitly deleted from the authorize URL's searchParams.",
    "ground_truth_files": [
      "packages/corsair/oauth/index.ts"
    ],
    "ground_truth_functions": [
      "generateOAuthUrl"
    ]
  },
  {
    "question": "Under what exact condition does the maybeStartConnectLoop function abort without starting the loop?",
    "ground_truth": "It aborts if the hub.projectApiKey does not exist or does not start with the prefix 'ck_dev_'.",
    "ground_truth_files": [
      "packages/corsair/core/index.ts"
    ],
    "ground_truth_functions": [
      "maybeStartConnectLoop"
    ]
  },
  {
    "question": "Which internal function is invoked to dynamically construct the CorsairClient instance when withTenant is called?",
    "ground_truth": "The buildCorsairClient function is called to construct the scoped instance.",
    "ground_truth_files": [
      "packages/corsair/core/index.ts"
    ],
    "ground_truth_functions": [
      "createCorsair"
    ]
  },
  {
    "question": "Which ORM method updates the status field of an existing event row?",
    "ground_truth": "The updateStatus method on the events client updates the status.",
    "ground_truth_files": [
      "packages/corsair/db/orm.ts"
    ],
    "ground_truth_functions": [
      "createEventsClient"
    ]
  },
  {
    "question": "Which ORM method searches for entities using a LIKE query against the entity_id?",
    "ground_truth": "The searchByEntityId method performs this search.",
    "ground_truth_files": [
      "packages/corsair/db/orm.ts"
    ],
    "ground_truth_functions": [
      "createEntitiesClient"
    ]
  },
  {
    "question": "Can you specify pagination offsets when fetching accounts by tenant, and if so, how?",
    "ground_truth": "Yes, the listByTenant method accepts an options object containing an 'offset' property.",
    "ground_truth_files": [
      "packages/corsair/db/orm.ts"
    ],
    "ground_truth_functions": [
      "createAccountsClient"
    ]
  },
  {
    "question": "Which factory function is responsible for scaffolding the generic CRUD operations (findById, findMany, create, update) for a table?",
    "ground_truth": "The createBaseTableClient function handles scaffolding the generic CRUD operations.",
    "ground_truth_files": [
      "packages/corsair/db/orm.ts"
    ],
    "ground_truth_functions": [
      "createBaseTableClient"
    ]
  },
  {
    "question": "Does findMatchingWebhook return the dot-separated path to the matched webhook?",
    "ground_truth": "It returns an array of string keys representing the path, which is later joined with dots by processWebhook.",
    "ground_truth_files": [
      "packages/corsair/webhooks/index.ts"
    ],
    "ground_truth_functions": [
      "findMatchingWebhook"
    ]
  },
  {
    "question": "What is the return type of the findById method on a CorsairTableClient if no record is found?",
    "ground_truth": "It returns null.",
    "ground_truth_files": [
      "packages/corsair/db/orm.ts"
    ],
    "ground_truth_functions": [
      "createBaseTableClient"
    ]
  },
  {
    "question": "Describe how findByTenantAndIntegration looks up an account without taking the integration's UUID directly.",
    "ground_truth": "It first queries the corsair_integrations table using the integrationName to fetch the integration's UUID, then uses that UUID along with the tenantId to query the corsair_accounts table via base.findOne.",
    "ground_truth_files": [
      "packages/corsair/db/orm.ts"
    ],
    "ground_truth_functions": [
      "createAccountsClient"
    ]
  },
  {
    "question": "How does processWebhook handle routing efficiency when the plugin option is explicitly provided (hinted by Hub)?",
    "ground_truth": "When hintedPlugin is present, it bypasses the pluginWebhookMatcher shape check and routes directly to the specified plugin's webhook tree, as Hub's routing is authoritative.",
    "ground_truth_files": [
      "packages/corsair/webhooks/index.ts"
    ],
    "ground_truth_functions": [
      "processWebhook"
    ]
  },
  {
    "question": "Explain the step-by-step logic upsertByEntityId uses to prevent duplicate inserts and handle updates.",
    "ground_truth": "upsertByEntityId first calls base.findOne to check for an existing entity matching account_id, entity_type, and entity_id. If found, it calls base.update on that row ID with the new version and data. If not found, it calls base.create to insert a new row.",
    "ground_truth_files": [
      "packages/corsair/db/orm.ts"
    ],
    "ground_truth_functions": [
      "createEntitiesClient"
    ]
  },
  {
    "question": "What critical cryptographic role does ensureAccount play during the OAuth callback flow?",
    "ground_truth": "If an account row does not exist, ensureAccount generates a new Data Encryption Key (DEK), encrypts it using the integration's Key Encryption Key (KEK), and stores the encrypted DEK in the new account row for future token encryptions.",
    "ground_truth_files": [
      "packages/corsair/oauth/index.ts"
    ],
    "ground_truth_functions": [
      "ensureAccount"
    ]
  },
  {
    "question": "How does processOAuthCallback programmatically differentiate and process a 'trusted' callback versus a standard callback?",
    "ground_truth": "For a standard callback, it calls verifyAndDecodeState to decrypt and validate the state string to extract the plugin and tenantId. For a trusted callback, it skips state verification entirely and reads the plugin and tenantId directly from the provided options object.",
    "ground_truth_files": [
      "packages/corsair/oauth/index.ts"
    ],
    "ground_truth_functions": [
      "processOAuthCallback"
    ]
  },
  {
    "question": "What condition dictates whether subscribeAndReport is executed at the end of the OAuth callback flow?",
    "ground_truth": "subscribeAndReport is only executed if the plugin object exposes a truthy 'subscribe' property, which is typical for class-1 providers like Outlook and Gmail that require token-authenticated webhook subscriptions.",
    "ground_truth_files": [
      "packages/corsair/oauth/index.ts"
    ],
    "ground_truth_functions": [
      "processOAuthCallback"
    ]
  },
  {
    "question": "How does the createCorsair factory behave when it is called with missing database or KEK configurations, but the caller tries to access integrationKeys?",
    "ground_truth": "It calls createMissingConfigProxy, which returns a Proxy object. This Proxy intercepts property accesses on the integrationKeys object and throws descriptive errors indicating that the database or KEK was not configured.",
    "ground_truth_files": [
      "packages/corsair/core/index.ts"
    ],
    "ground_truth_functions": [
      "createCorsair"
    ]
  },
  {
    "question": "What specific fields are mutated or populated when buildGoogleChannelBody detects a Google Drive resource URI?",
    "ground_truth": "It populates a notification object with x-goog-resource-id, x-goog-resource-state, x-goog-resource-uri, x-goog-channel-id, and x-goog-channel-expiration. Specifically for Drive, it appends a 'kind' property set to 'drive#change' before base64-encoding the JSON payload.",
    "ground_truth_files": [
      "packages/corsair/webhooks/index.ts"
    ],
    "ground_truth_functions": [
      "buildGoogleChannelBody"
    ]
  },
  {
    "question": "How does createBaseTableClient enforce strict runtime type safety on rows returned from the database?",
    "ground_truth": "It looks up the Zod schema associated with the tableName via getTableSchema. Inside the parseRow and parseRowFromRecord utilities, it executes schema.parse() on the raw database result to validate and infer the strict RowType.",
    "ground_truth_files": [
      "packages/corsair/db/orm.ts"
    ],
    "ground_truth_functions": [
      "createBaseTableClient"
    ]
  },
  {
    "question": "In processWebhook, how are response payloads constructed if a matching webhook handler returns a returnToSender object?",
    "ground_truth": "If returnToSender exists, processWebhook constructs a response object containing the spread properties of returnToSender and sets 'success' to true. It also conditionally merges in 'responseHeaders' to the final WebhookFilterResult if they were provided by the handler.",
    "ground_truth_files": [
      "packages/corsair/webhooks/index.ts"
    ],
    "ground_truth_functions": [
      "processWebhook"
    ]
  },
  {
    "question": "How does the ORM layer internally translate the 'in' array filter property into compatible Kysely query operators?",
    "ground_truth": "The buildWhere function identifies that the value is an object containing an 'in' array. It maps this by pushing a CorsairWhere object with operator 'in'. Later, applyCorsairWhere loops over this and executes Kysely's .where(column, 'in', arrayValue) method.",
    "ground_truth_files": [
      "packages/corsair/db/orm.ts"
    ],
    "ground_truth_functions": [
      "buildWhere",
      "applyCorsairWhere"
    ]
  },
  {
    "question": "What are the architectural and security implications of utilizing the 'trusted' flag inside processOAuthCallback, and why does the Hub platform rely on it?",
    "ground_truth": "The trusted flag forces processOAuthCallback to bypass HMAC signature verification of the state parameter. The Hub platform relies on this because Hub manages OAuth states as opaque session IDs and never possesses the tenant's Key Encryption Key (KEK) to sign them. Consequently, the caller assumes full responsibility for cryptographically verifying the Hub's request signature before invoking processOAuthCallback.",
    "ground_truth_files": [
      "packages/corsair/oauth/index.ts"
    ],
    "ground_truth_functions": [
      "processOAuthCallback"
    ]
  },
  {
    "question": "In packages/corsair/core/index.ts, when configuring the createCorsair factory, how do you pass the tenantId property directly into the root CorsairIntegration config object?",
    "ground_truth": "You cannot pass the tenantId in the root CorsairIntegration config object. When multiTenancy is true, the tenantId is strictly passed dynamically via the withTenant(tenantId) method on the returned CorsairTenantWrapper.",
    "ground_truth_files": [
      "packages/corsair/core/index.ts"
    ],
    "ground_truth_functions": [
      "createCorsair"
    ]
  },
  {
    "question": "Which parameter in the generateOAuthUrl function's options allows you to specify a customTokenStorage adapter to override the default database writes?",
    "ground_truth": "There is no customTokenStorage parameter in generateOAuthUrl or the ProcessOAuthCallbackOptions. Token storage in the Corsair architecture strictly relies on the Kysely database instance provided during the initial createCorsair initialization.",
    "ground_truth_files": [
      "packages/corsair/oauth/index.ts"
    ],
    "ground_truth_functions": [
      "generateOAuthUrl"
    ]
  },
  {
    "question": "In the processWebhook function, how do you configure the StripeSignatureValidator interface inside the WebhookFilterResult to automatically reject invalid Stripe events?",
    "ground_truth": "You cannot configure a StripeSignatureValidator in processWebhook. The processWebhook function handles generic webhook routing and does not perform signature validation; signature validation must be handled either by the caller middleware before invocation or internally by the individual plugin handlers.",
    "ground_truth_files": [
      "packages/corsair/webhooks/index.ts"
    ],
    "ground_truth_functions": [
      "processWebhook"
    ]
  }
]

def score_with_llm(question: str, agent_answer: str, ground_truth: str, retrieved_context: list) -> dict:
    try:
        client = get_gemini_client()
    except Exception:
        return {"relevance": 0.0, "faithfulness": 0.0, "accuracy": 0.0}
        
    context_str = ""
    for c in retrieved_context:
        file_path = c.get("metadata", {}).get("file_path", "unknown")
        content = c.get("content", "")
        # Sanitize code content: raw backslashes in TypeScript code break json.loads
        # when Gemini embeds the context inside a JSON response ("Invalid \escape" error).
        # Replace lone backslashes with a safe placeholder so json.loads never sees them.
        safe_content = content.replace("\\", "/")
        context_str += f"--- FILE: {file_path} ---\n{safe_content}\n"
        
    import time
    import re
    
    def run_prompt(prompt_text):
        nonlocal client
        for i in range(5):
            try:
                response = client.models.generate_content(
                    model="gemini-3.1-flash-lite",
                    contents=prompt_text,
                    config=types.GenerateContentConfig(response_mime_type="application/json")
                )
                raw = response.text.strip()
                # Fix for 'Extra data' error: Gemini sometimes outputs valid JSON
                # followed by extra trailing text. Extract only the FIRST complete
                # JSON object/array instead of passing the whole string to json.loads.
                match = re.search(r'(\{.*\}|\[.*\])', raw, re.DOTALL)
                if match:
                    return json.loads(match.group(1))
                return json.loads(raw)  # fallback: try raw if no match
            except Exception as e:
                if i == 4:
                    print(f"Error scoring with LLM: {e}")
                    return None
                print(f"Gemini API rate limit hit in evaluator. Fetching new key and retrying... ({e})")
                time.sleep(5)
                try:
                    from utils import get_gemini_client
                    client = get_gemini_client()
                except: pass
        return None

    # 1. Faithfulness
    prompt_faithfulness = f"""You are a strict fact-checker evaluating whether a generated answer is fully supported by the provided source context. Do not be lenient — your job is to catch unsupported claims, not to give the benefit of the doubt.

SOURCE CONTEXT:
{context_str}

GENERATED ANSWER:
{agent_answer}

Instructions:
1. Break the generated answer into individual atomic claims (one factual statement per claim).
2. For each claim, determine if it is:
   - SUPPORTED: directly and explicitly backed by the source context
   - UNSUPPORTED: not present in the source context, even if it sounds plausible or is generally true about code in general
   - CONTRADICTED: source context actually says something different
3. A claim is only SUPPORTED if you can point to the specific part of the context that backs it. If you cannot point to specific supporting text, mark it UNSUPPORTED.
4. Do not give credit for claims that are "reasonable inferences" unless the inference is a direct, unambiguous logical consequence of the context (e.g. simple code logic, not speculation about intent).

Output strict JSON:
{{
  "claims": [
    {{"claim": "...", "verdict": "SUPPORTED|UNSUPPORTED|CONTRADICTED", "evidence": "quote or 'none found'"}}
  ],
  "faithfulness_score": 0.0,
  "summary": "one sentence explaining the score"
}}"""

    # 2. Relevance
    prompt_relevance = f"""You are a strict evaluator checking whether a generated answer actually and fully addresses the user's specific query. Do not reward answers that are merely topically related — they must directly answer what was asked.

USER QUERY:
{question}

GENERATED ANSWER:
{agent_answer}

Score on this rubric (pick exactly one):
- 1.0 = Directly and completely answers every part of the query, with no significant omissions
- 0.75 = Answers the main question but misses a secondary part of a multi-part query, or is slightly less specific than the query warranted
- 0.5 = Partially relevant — touches the right topic/area but doesn't actually resolve what was asked
- 0.25 = Loosely related to the query's general subject but fails to address the actual question
- 0.0 = Off-topic, generic, or answers a different question than the one asked

Be strict: if the query asks a structural question (e.g. "what calls this function") and the answer gives a general description of the function instead of listing callers, that is NOT a 1.0 — score it 0.25-0.5 depending on how far off it is.

Output strict JSON:
{{
  "score": 0.0,
  "reasoning": "specific explanation citing what was asked vs. what was answered",
  "missed_aspects": ["list any part of the query that went unaddressed, or empty list if none"]
}}"""

    # 3. Accuracy
    prompt_accuracy = f"""You are a strict evaluator comparing a generated answer against a gold-standard reference answer for factual correctness and completeness.

QUERY:
{question}

GENERATED ANSWER:
{agent_answer}

REFERENCE (GROUND TRUTH) ANSWER:
{ground_truth}

Instructions:
1. Identify the key facts/claims present in the reference answer that any correct response must include.
2. Check whether the generated answer includes each of these key facts, and whether it introduces any facts that conflict with the reference.
3. If the reference asserts something does NOT exist, check whether the generated answer correctly denies it, and treat any confident invented detail as a contradiction.
4. Do not reward a generated answer for being verbose or "sounding confident" — score strictly on factual overlap with the reference and absence of contradictions.

Output strict JSON:
{{
  "key_facts_in_reference": ["fact 1", "fact 2"],
  "key_facts_covered": ["which of the above were present in the generated answer"],
  "contradictions": ["any claims in the generated answer that conflict with the reference, or empty list"],
  "accuracy_score": 0.0,
  "reasoning": "one to two sentences explaining the score"
}}"""

    res_faith = run_prompt(prompt_faithfulness)
    res_rel = run_prompt(prompt_relevance)
    res_acc = run_prompt(prompt_accuracy)

    faith_score = float(res_faith.get("faithfulness_score", 0.0)) if res_faith else 0.0
    rel_score = float(res_rel.get("score", 0.0)) if res_rel else 0.0
    acc_score = float(res_acc.get("accuracy_score", 0.0)) if res_acc else 0.0

    return {
        "relevance": rel_score,
        "faithfulness": faith_score,
        "accuracy": acc_score
    }

