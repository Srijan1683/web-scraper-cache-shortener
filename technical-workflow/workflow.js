const diagram = document.querySelector("#diagram");
const arrowLayer = document.querySelector("#arrow-layer");
const scenarioButtons = [...document.querySelectorAll(".scenario-button")];
const replayButton = document.querySelector("#replay-button");
const resetButton = document.querySelector("#reset-button");
const statusPanel = document.querySelector("#status-panel");
const statusPill = document.querySelector("#status-pill");
const statusTitle = document.querySelector("#status-title");
const statusText = document.querySelector("#status-text");

const connectors = [
  { id: "p-request-p-validate", from: "p-request", to: "p-validate" },
  { id: "p-validate-p-cache", from: "p-validate", to: "p-cache" },
  { id: "p-cache-p-fetch", from: "p-cache", to: "p-fetch" },
  { id: "p-fetch-p-html", from: "p-fetch", to: "p-html" },
  { id: "p-html-p-parse", from: "p-html", to: "p-parse" },
  { id: "p-parse-p-extract", from: "p-parse", to: "p-extract" },
  { id: "p-extract-p-code", from: "p-extract", to: "p-code" },
  { id: "p-code-p-build", from: "p-code", to: "p-build" },
  { id: "p-build-p-store", from: "p-build", to: "p-store" },
  { id: "p-store-p-response", from: "p-store", to: "p-response" },
  { id: "p-response-p-render", from: "p-response", to: "p-render" },
  { id: "p-render-m-request", from: "p-render", to: "m-request", dashed: true },
  { id: "p-cache-p-cached", from: "p-cache", to: "p-cached" },
  { id: "p-cached-p-cached-render", from: "p-cached", to: "p-cached-render" },
  { id: "p-validate-p-error", from: "p-validate", to: "p-error" },
  { id: "p-fetch-p-error", from: "p-fetch", to: "p-error" },
  { id: "p-html-p-error", from: "p-html", to: "p-error" },
  { id: "m-request-m-validate", from: "m-request", to: "m-validate" },
  { id: "m-validate-m-fetch", from: "m-validate", to: "m-fetch" },
  { id: "m-fetch-m-html", from: "m-fetch", to: "m-html" },
  { id: "m-html-m-convert", from: "m-html", to: "m-convert" },
  { id: "m-convert-m-cache", from: "m-convert", to: "m-cache", dashed: true },
  { id: "m-cache-m-attachment", from: "m-cache", to: "m-attachment" },
  { id: "m-attachment-m-download", from: "m-attachment", to: "m-download" },
  { id: "m-cache-s-request", from: "m-cache", to: "s-request", dashed: true },
  { id: "m-attachment-s-request", from: "m-attachment", to: "s-request", dashed: true },
  { id: "m-validate-m-error", from: "m-validate", to: "m-error" },
  { id: "m-fetch-m-error", from: "m-fetch", to: "m-error" },
  { id: "m-html-m-error", from: "m-html", to: "m-error" },
  { id: "s-request-s-load", from: "s-request", to: "s-load", dashed: true },
  { id: "s-load-s-cache", from: "s-load", to: "s-cache", dashed: true },
  { id: "s-cache-s-openai", from: "s-cache", to: "s-openai", dashed: true },
  { id: "s-openai-s-store", from: "s-openai", to: "s-store", dashed: true },
  { id: "s-store-s-summary", from: "s-store", to: "s-summary", dashed: true },
  { id: "s-cache-s-cached", from: "s-cache", to: "s-cached", dashed: true },
  { id: "s-cached-s-cached-return", from: "s-cached", to: "s-cached-return", dashed: true },
  { id: "s-openai-s-error", from: "s-openai", to: "s-error", dashed: true },
];

const scenarios = {
  "preview-miss": {
    title: "POST /scrape",
    initial: "Simulating the full preview path with a cache miss.",
    finalState: "complete",
    steps: [
      { node: "p-request", note: "Request enters the FastAPI preview route." },
      { node: "p-validate", connector: "p-request-p-validate", note: "The URL is trimmed and validated for HTTPS." },
      { node: "p-cache", connector: "p-validate-p-cache", note: "The cache is checked for an existing structured result." },
      { node: "p-fetch", connector: "p-cache-p-fetch", note: "Cache miss. The backend fetches the page." },
      { node: "p-html", connector: "p-fetch-p-html", note: "The response content type is verified as HTML." },
      { node: "p-parse", connector: "p-html-p-parse", note: "HTML is parsed with BeautifulSoup." },
      { node: "p-extract", connector: "p-parse-p-extract", note: "Title, description, links, images, and headings are extracted." },
      { node: "p-code", connector: "p-extract-p-code", note: "A deterministic short code is generated." },
      { node: "p-build", connector: "p-code-p-build", note: "The structured result object is assembled." },
      { node: "p-store", connector: "p-build-p-store", note: "The result is stored in cache." },
      { node: "p-response", connector: "p-store-p-response", note: "JSON is returned to the caller." },
      { node: "p-render", connector: "p-response-p-render", note: "The preview UI renders the final response." },
    ],
  },
  "preview-hit": {
    title: "Cache Hit",
    initial: "Running the short preview path from cache.",
    finalState: "complete",
    steps: [
      { node: "p-request", note: "Preview request enters the route." },
      { node: "p-validate", connector: "p-request-p-validate", note: "The URL passes the initial validation layer." },
      { node: "p-cache", connector: "p-validate-p-cache", note: "The cache lookup succeeds immediately." },
      { node: "p-cached", connector: "p-cache-p-cached", note: "The cached result is returned without a network fetch." },
      { node: "p-cached-render", connector: "p-cached-p-cached-render", note: "The frontend renders the cached preview." },
    ],
  },
  "markdown-success": {
    title: "POST /scrape/markdown",
    initial: "Tracing the markdown export path.",
    finalState: "complete",
    steps: [
      { node: "m-request", note: "The markdown route receives the target URL." },
      { node: "m-request", connector: "p-render-m-request", note: "Markdown export is typically triggered after the preview is reviewed." },
      { node: "m-validate", connector: "m-request-m-validate", note: "The URL is validated before fetching." },
      { node: "m-fetch", connector: "m-validate-m-fetch", note: "The page is fetched from the source site." },
      { node: "m-html", connector: "m-fetch-m-html", note: "The response is checked for HTML content." },
      { node: "m-convert", connector: "m-html-m-convert", note: "The HTML is converted into markdown." },
      { node: "m-cache", connector: "m-convert-m-cache", note: "Optional helper path for storing markdown in cache." },
      { node: "m-attachment", connector: "m-cache-m-attachment", note: "The response is packaged as a markdown attachment." },
      { node: "m-download", connector: "m-attachment-m-download", note: "The browser downloads the generated .md file." },
    ],
  },
  "preview-error": {
    title: "Preview Error",
    initial: "Tracing a failed preview request.",
    finalState: "error",
    steps: [
      { node: "p-request", note: "The preview route receives the request." },
      { node: "p-validate", connector: "p-request-p-validate", note: "Validation inspects the URL." },
      { node: "p-error", connector: "p-validate-p-error", note: "Invalid or unsafe input triggers HTTP 400.", error: true },
    ],
  },
  "markdown-error": {
    title: "Markdown Error",
    initial: "Tracing a markdown failure branch.",
    finalState: "error",
    steps: [
      { node: "m-request", note: "The markdown route is triggered." },
      { node: "m-validate", connector: "m-request-m-validate", note: "Input validation completes successfully." },
      { node: "m-fetch", connector: "m-validate-m-fetch", note: "The backend begins fetching the page." },
      { node: "m-error", connector: "m-fetch-m-error", note: "Timeout, HTTP failure, or a non-HTML response ends the request.", error: true },
    ],
  },
  "summary-success": {
    title: "AI Summary",
    initial: "Tracing the planned OpenAI summary flow.",
    finalState: "complete",
    steps: [
      { node: "s-request", note: "A technical summary run is triggered after markdown is available." },
      { node: "s-request", connector: "m-cache-s-request", note: "The summary pipeline starts from fresh or cached markdown." },
      { node: "s-load", connector: "s-request-s-load", note: "Markdown is loaded from a fresh scrape or cache." },
      { node: "s-cache", connector: "s-load-s-cache", note: "A summary cache is checked first." },
      { node: "s-openai", connector: "s-cache-s-openai", note: "Cache miss. The markdown is sent through the OpenAI SDK." },
      { node: "s-store", connector: "s-openai-s-store", note: "The generated summary is stored for reuse." },
      { node: "s-summary", connector: "s-store-s-summary", note: "The summary is returned to the technical caller." },
    ],
  },
  "summary-error": {
    title: "Summary Error",
    initial: "Tracing the planned summary failure branch.",
    finalState: "error",
    steps: [
      { node: "s-request", note: "A summary run is started." },
      { node: "s-request", connector: "m-cache-s-request", note: "The summary branch is entered from the markdown stage." },
      { node: "s-load", connector: "s-request-s-load", note: "Markdown is loaded for summarisation." },
      { node: "s-cache", connector: "s-load-s-cache", note: "No cached summary is available." },
      { node: "s-openai", connector: "s-cache-s-openai", note: "The OpenAI SDK call begins." },
      { node: "s-error", connector: "s-openai-s-error", note: "Rate limit, network failure, or model error stops the flow.", error: true },
    ],
  },
};

let activeScenarioKey = "preview-miss";
let animationRun = 0;

function clearState() {
  document.querySelectorAll(".node").forEach((node) => {
    node.classList.remove("is-active", "is-complete", "is-error", "is-terminal");
  });

  arrowLayer.querySelectorAll(".arrow").forEach((arrow) => {
    arrow.classList.remove("is-active", "is-complete", "is-error");
  });
}

function setStatus(state, title, text) {
  statusPanel.dataset.state = state;
  statusPill.textContent = state === "idle" ? "Idle" : state === "error" ? "Error" : state === "running" ? "Running" : "Complete";
  statusTitle.textContent = title;
  statusText.textContent = text;
}

function wait(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function setSelectedScenario(key) {
  activeScenarioKey = key;
  scenarioButtons.forEach((button) => {
    button.classList.toggle("is-selected", button.dataset.scenario === key);
  });
}

function getConnectorElement(id) {
  return arrowLayer.querySelector(`[data-connector-id="${id}"]`);
}

function getAnchorPoint(rect, side, hostRect) {
  if (side === "right") {
    return { x: rect.right - hostRect.left, y: rect.top - hostRect.top + rect.height / 2 };
  }
  if (side === "left") {
    return { x: rect.left - hostRect.left, y: rect.top - hostRect.top + rect.height / 2 };
  }
  if (side === "bottom") {
    return { x: rect.left - hostRect.left + rect.width / 2, y: rect.bottom - hostRect.top };
  }
  return { x: rect.left - hostRect.left + rect.width / 2, y: rect.top - hostRect.top };
}

function buildConnectorPath(sourceRect, targetRect, hostRect) {
  const sourceCenter = {
    x: sourceRect.left - hostRect.left + sourceRect.width / 2,
    y: sourceRect.top - hostRect.top + sourceRect.height / 2,
  };
  const targetCenter = {
    x: targetRect.left - hostRect.left + targetRect.width / 2,
    y: targetRect.top - hostRect.top + targetRect.height / 2,
  };

  const horizontal = Math.abs(targetCenter.x - sourceCenter.x) >= Math.abs(targetCenter.y - sourceCenter.y);
  const start = getAnchorPoint(sourceRect, horizontal ? (targetCenter.x >= sourceCenter.x ? "right" : "left") : (targetCenter.y >= sourceCenter.y ? "bottom" : "top"), hostRect);
  const end = getAnchorPoint(targetRect, horizontal ? (targetCenter.x >= sourceCenter.x ? "left" : "right") : (targetCenter.y >= sourceCenter.y ? "top" : "bottom"), hostRect);

  if (horizontal) {
    const bend = (start.x + end.x) / 2;
    return `M ${start.x} ${start.y} L ${bend} ${start.y} L ${bend} ${end.y} L ${end.x} ${end.y}`;
  }

  const bend = (start.y + end.y) / 2;
  return `M ${start.x} ${start.y} L ${start.x} ${bend} L ${end.x} ${bend} L ${end.x} ${end.y}`;
}

function drawConnectors() {
  arrowLayer.querySelectorAll(".arrow").forEach((path) => path.remove());

  const hostRect = diagram.getBoundingClientRect();
  arrowLayer.setAttribute("viewBox", `0 0 ${Math.ceil(hostRect.width)} ${Math.ceil(hostRect.height)}`);

  connectors.forEach((connector) => {
    const from = document.getElementById(connector.from);
    const to = document.getElementById(connector.to);
    if (!from || !to) {
      return;
    }

    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", buildConnectorPath(from.getBoundingClientRect(), to.getBoundingClientRect(), hostRect));
    path.setAttribute("class", connector.dashed ? "arrow arrow-dashed" : "arrow");
    path.dataset.connectorId = connector.id;
    arrowLayer.appendChild(path);
  });
}

async function runScenario(key) {
  const scenario = scenarios[key];
  if (!scenario) {
    return;
  }

  animationRun += 1;
  const runId = animationRun;

  setSelectedScenario(key);
  clearState();
  setStatus("running", scenario.title, scenario.initial);

  for (const step of scenario.steps) {
    if (runId !== animationRun) {
      return;
    }

    const node = document.getElementById(step.node);
    const connector = step.connector ? getConnectorElement(step.connector) : null;
    const stateClass = step.error ? "is-error" : "is-complete";

    if (connector) {
      connector.classList.remove("is-complete", "is-error");
      connector.classList.add(step.error ? "is-error" : "is-active");
    }

    if (node) {
      node.classList.remove("is-complete", "is-error", "is-terminal");
      node.classList.add("is-active");
    }

    setStatus("running", scenario.title, step.note);
    await wait(540);

    if (runId !== animationRun) {
      return;
    }

    if (connector) {
      connector.classList.remove("is-active");
      connector.classList.add(stateClass);
    }

    if (node) {
      node.classList.remove("is-active");
      node.classList.add(stateClass);
      if (node.classList.contains("node-terminal")) {
        node.classList.add("is-terminal");
      }
    }
  }

  const outcomeText = scenario.finalState === "error" ? "Error branch complete." : "Flow complete.";
  setStatus(scenario.finalState, scenario.title, outcomeText);
}

function resetDiagram() {
  animationRun += 1;
  clearState();
  setStatus("idle", "Waiting for a scenario", "Run any path to watch nodes and arrows move through the pipeline.");
}

scenarioButtons.forEach((button) => {
  button.addEventListener("click", () => runScenario(button.dataset.scenario));
});

replayButton.addEventListener("click", () => runScenario(activeScenarioKey));
resetButton.addEventListener("click", resetDiagram);

window.addEventListener("resize", drawConnectors);
window.addEventListener("load", () => {
  drawConnectors();
  runScenario(activeScenarioKey);
});
