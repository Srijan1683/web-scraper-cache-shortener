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
  { id: "j-submit-j-validate", from: "j-submit", to: "j-validate" },
  { id: "j-validate-j-check", from: "j-validate", to: "j-check" },
  { id: "j-check-j-cached", from: "j-check", to: "j-cached", state: "cache" },
  { id: "j-check-j-queue", from: "j-check", to: "j-queue" },
  { id: "j-queue-j-crawl", from: "j-queue", to: "j-crawl" },
  { id: "j-crawl-j-result", from: "j-crawl", to: "j-result" },
  { id: "j-result-j-summary", from: "j-result", to: "j-summary" },
  { id: "j-summary-j-markdown", from: "j-summary", to: "j-markdown" },
  { id: "j-markdown-j-summary-cache", from: "j-markdown", to: "j-summary-cache" },
  { id: "j-summary-cache-j-complete", from: "j-summary-cache", to: "j-complete" },
  { id: "j-crawl-j-failed", from: "j-crawl", to: "j-failed" },
  { id: "j-summary-j-failed", from: "j-summary", to: "j-failed" },
  { id: "j-complete-q-job", from: "j-complete", to: "q-job", state: "cache" },
  { id: "q-job-q-job-return", from: "q-job", to: "q-job-return" },
  { id: "j-complete-q-summary", from: "j-complete", to: "q-summary", state: "cache" },
  { id: "q-summary-q-summary-return", from: "q-summary", to: "q-summary-return" },
  { id: "j-complete-q-delete", from: "j-complete", to: "q-delete", state: "cache" },
  { id: "q-delete-q-delete-return", from: "q-delete", to: "q-delete-return" },
  { id: "j-summary-u-markdown", from: "j-summary", to: "u-markdown", state: "cache" },
  { id: "u-markdown-u-markdown-return", from: "u-markdown", to: "u-markdown-return" },
  { id: "u-shorten-u-redirect", from: "u-shorten", to: "u-redirect" },
  { id: "u-redirect-u-stats", from: "u-redirect", to: "u-stats" },
  { id: "u-health-u-health-return", from: "u-health", to: "u-health-return" }
];

const scenarios = {
  "scrape-queued": {
    title: "POST /scrape",
    initial: "Tracing the queued job path through scrape, markdown, and summary generation.",
    finalState: "complete",
    steps: [
      { node: "j-submit", note: "A scrape request enters with a URL and summary type." },
      { node: "j-validate", connector: "j-submit-j-validate", note: "Input passes request validation and scraper URL checks." },
      { node: "j-check", connector: "j-validate-j-check", note: "The backend checks for an existing job or fully cached assets." },
      { node: "j-queue", connector: "j-check-j-queue", note: "No complete reuse path is found, so a queued job is created." },
      { node: "j-crawl", connector: "j-queue-j-crawl", note: "Background processing starts and the job moves into scraping." },
      { node: "j-result", connector: "j-crawl-j-result", note: "Parsed scrape data is packaged and cached as a scrape result." },
      { node: "j-summary", connector: "j-result-j-summary", note: "The pipeline moves into summarising after the scrape result is ready." },
      { node: "j-markdown", connector: "j-summary-j-markdown", note: "Markdown is reused from cache or freshly built for the job." },
      { node: "j-summary-cache", connector: "j-markdown-j-summary-cache", note: "Summary cache is checked before calling the provider." },
      { node: "j-complete", connector: "j-summary-cache-j-complete", note: "Summary and result are attached and the job is persisted as completed." }
    ]
  },
  "scrape-cached": {
    title: "Cached Return",
    initial: "Tracing the immediate reuse path for an existing cached job.",
    finalState: "complete",
    steps: [
      { node: "j-submit", note: "A repeated scrape request enters the same route." },
      { node: "j-validate", connector: "j-submit-j-validate", note: "Validation still runs first." },
      { node: "j-check", connector: "j-validate-j-check", note: "The URL and summary type are matched against cached job state." },
      { node: "j-cached", connector: "j-check-j-cached", note: "The backend returns the existing job immediately instead of reprocessing.", connectorState: "cache" }
    ]
  },
  "job-summary": {
    title: "GET /scrape/{job_id}/summary",
    initial: "Tracing summary lookup after a job has already completed.",
    finalState: "complete",
    steps: [
      { node: "j-complete", note: "The scrape job has already finished and stored its final summary." },
      { node: "q-summary", connector: "j-complete-q-summary", note: "This follow-up route reads from the completed job record.", connectorState: "cache" },
      { node: "q-summary-return", connector: "q-summary-q-summary-return", note: "The summarization payload is returned if available, otherwise the route can emit 409." }
    ]
  },
  "markdown-export": {
    title: "POST /scrape/markdown",
    initial: "Tracing the markdown utility path used alongside the core job pipeline.",
    finalState: "complete",
    steps: [
      { node: "j-summary", note: "Markdown sits beside the summarising stage in the main pipeline." },
      { node: "u-markdown", connector: "j-summary-u-markdown", note: "The utility endpoint reads cached markdown or builds it on demand.", connectorState: "cache" },
      { node: "u-markdown-return", connector: "u-markdown-u-markdown-return", note: "A markdown attachment is returned for download." }
    ]
  },
  "delete-job": {
    title: "DELETE /scrape/{job_id}",
    initial: "Tracing cleanup after a job has already completed or been stored.",
    finalState: "complete",
    steps: [
      { node: "j-complete", note: "A stored job and its related caches are already available." },
      { node: "q-delete", connector: "j-complete-q-delete", note: "This follow-up route removes the job record plus URL-linked cache entries.", connectorState: "cache" },
      { node: "q-delete-return", connector: "q-delete-q-delete-return", note: "The API returns 204 after cleanup completes." }
    ]
  },
  shortener: {
    title: "Shortener",
    initial: "Tracing short URL creation, redirect, and stats lookup.",
    finalState: "complete",
    steps: [
      { node: "u-shorten", note: "A short code is generated and cached for the original URL." },
      { node: "u-redirect", connector: "u-shorten-u-redirect", note: "Public redirect reads the short code and increments clicks." },
      { node: "u-stats", connector: "u-redirect-u-stats", note: "Stats lookup returns the click count and short URL metadata." },
      { node: "u-health", note: "Operationally, health remains independent of short-link traffic." },
      { node: "u-health-return", connector: "u-health-u-health-return", note: "Health exposes API status and Redis connectivity state." }
    ]
  },
  "scrape-failed": {
    title: "Failure",
    initial: "Tracing a job that fails during scrape or summary generation.",
    finalState: "error",
    steps: [
      { node: "j-submit", note: "A scrape request enters the pipeline." },
      { node: "j-validate", connector: "j-submit-j-validate", note: "Input validation succeeds and processing begins." },
      { node: "j-check", connector: "j-validate-j-check", note: "No cached completion is available." },
      { node: "j-queue", connector: "j-check-j-queue", note: "A background job is created." },
      { node: "j-crawl", connector: "j-queue-j-crawl", note: "The scraper fetches the target page." },
      { node: "j-failed", connector: "j-crawl-j-failed", note: "Fetch, HTML validation, or provider failure pushes the job into failed state.", error: true }
    ]
  }
};

let activeScenarioKey = "scrape-queued";
let animationRun = 0;

function clearState() {
  document.querySelectorAll(".node").forEach((node) => {
    node.classList.remove("is-active", "is-complete", "is-error");
  });

  arrowLayer.querySelectorAll(".arrow").forEach((arrow) => {
    arrow.classList.remove("is-active", "is-complete", "is-error", "is-cache");
    if (arrow.dataset.baseState === "cache") {
      arrow.classList.add("is-cache");
    }
  });
}

function setStatus(state, title, text) {
  statusPanel.dataset.state = state;
  statusPill.textContent =
    state === "idle" ? "Idle" : state === "error" ? "Error" : state === "running" ? "Running" : "Complete";
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
    y: sourceRect.top - hostRect.top + sourceRect.height / 2
  };
  const targetCenter = {
    x: targetRect.left - hostRect.left + targetRect.width / 2,
    y: targetRect.top - hostRect.top + targetRect.height / 2
  };

  const horizontal = Math.abs(targetCenter.x - sourceCenter.x) > Math.abs(targetCenter.y - sourceCenter.y);
  const start = getAnchorPoint(
    sourceRect,
    horizontal ? (targetCenter.x >= sourceCenter.x ? "right" : "left") : (targetCenter.y >= sourceCenter.y ? "bottom" : "top"),
    hostRect
  );
  const end = getAnchorPoint(
    targetRect,
    horizontal ? (targetCenter.x >= sourceCenter.x ? "left" : "right") : (targetCenter.y >= sourceCenter.y ? "top" : "bottom"),
    hostRect
  );

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
    path.setAttribute("class", "arrow");
    path.dataset.connectorId = connector.id;
    path.dataset.baseState = connector.state || "";
    if (connector.state === "cache") {
      path.classList.add("is-cache");
    }
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
    const connectorState = step.error ? "is-error" : step.connectorState === "cache" ? "is-cache" : "is-complete";
    const nodeState = step.error ? "is-error" : "is-complete";

    if (connector) {
      connector.classList.remove("is-complete", "is-error", "is-cache");
      connector.classList.add("is-active");
    }

    if (node) {
      node.classList.remove("is-complete", "is-error");
      node.classList.add("is-active");
    }

    setStatus("running", scenario.title, step.note);
    await wait(460);

    if (runId !== animationRun) {
      return;
    }

    if (connector) {
      connector.classList.remove("is-active");
      connector.classList.add(connectorState);
    }

    if (node) {
      node.classList.remove("is-active");
      node.classList.add(nodeState);
    }
  }

  const outcomeText = scenario.finalState === "error" ? "Failure branch complete." : "Flow complete.";
  setStatus(scenario.finalState, scenario.title, outcomeText);
}

function resetDiagram() {
  animationRun += 1;
  clearState();
  setStatus("idle", "Waiting for a scenario", "Select a backend path to animate nodes and connector states.");
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
