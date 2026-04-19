const nodeButtons = [...document.querySelectorAll(".node")];
const diagramCanvas = document.querySelector(".diagram-canvas");
const edgeLayer = document.querySelector("#edge-layer");
const dotLayer = document.querySelector("#dot-layer");
const runSuccessButton = document.querySelector("#run-success");
const runErrorButton = document.querySelector("#run-error");
const resetButton = document.querySelector("#reset-view");

const detailTitle = document.querySelector("#detail-title");
const detailSummary = document.querySelector("#detail-summary");
const detailInputs = document.querySelector("#detail-inputs");
const detailOutputs = document.querySelector("#detail-outputs");
const detailFailures = document.querySelector("#detail-failures");
const detailNotes = document.querySelector("#detail-notes");
const pathState = document.querySelector("#path-state");

const EDGE_CONFIG = {
  "start-validate": { from: "start", to: "validate", type: "happy", route: "horizontal" },
  "validate-cache": { from: "validate", to: "cache-decision", type: "happy", route: "horizontal" },
  "cache-hit-response": { from: "cache-decision", to: "response", type: "happy", route: "horizontal" },
  "response-end": { from: "response", to: "end", type: "happy", route: "horizontal" },
  "cache-miss-scrape": { from: "cache-decision", to: "scrape", type: "happy", route: "vertical" },
  "scrape-buildjson": { from: "scrape", to: "build-json", type: "happy", route: "horizontal" },
  "buildjson-response": { from: "build-json", to: "response", type: "happy", route: "vertical-up" },
  "buildjson-ttl": { from: "build-json", to: "summary-store", type: "async", route: "curve-down" },
  "scrape-markdown": { from: "scrape", to: "markdown", type: "async", route: "curve-down-left" },
  "markdown-ttl": { from: "markdown", to: "summary-store", type: "async", route: "horizontal" },
  "ttl-summary": { from: "summary-store", to: "summary", type: "async", route: "horizontal" },
  "summary-store": { from: "summary", to: "summary-store", type: "async", route: "curve-back" },
  "validate-error": { from: "validate", to: "invalid-request", type: "error", route: "vertical" },
  "scrape-error": { from: "scrape", to: "scrape-failure", type: "error", route: "vertical" },
  "summary-error": { from: "summary", to: "summary-failure", type: "error", route: "vertical" },
};

const NODE_PATHS = {
  start: { nodes: ["start"], edges: [] },
  validate: { nodes: ["start", "validate"], edges: ["start-validate"] },
  "cache-decision": { nodes: ["start", "validate", "cache-decision"], edges: ["start-validate", "validate-cache"] },
  response: { nodes: ["start", "validate", "cache-decision", "response"], edges: ["start-validate", "validate-cache", "cache-hit-response"] },
  end: { nodes: ["start", "validate", "cache-decision", "response", "end"], edges: ["start-validate", "validate-cache", "cache-hit-response", "response-end"] },
  scrape: { nodes: ["start", "validate", "cache-decision", "scrape"], edges: ["start-validate", "validate-cache", "cache-miss-scrape"] },
  "build-json": { nodes: ["start", "validate", "cache-decision", "scrape", "build-json"], edges: ["start-validate", "validate-cache", "cache-miss-scrape", "scrape-buildjson"] },
  markdown: { nodes: ["start", "validate", "cache-decision", "scrape", "markdown"], edges: ["start-validate", "validate-cache", "cache-miss-scrape", "scrape-markdown"] },
  "summary-store": { nodes: ["start", "validate", "cache-decision", "scrape", "build-json", "markdown", "summary-store"], edges: ["start-validate", "validate-cache", "cache-miss-scrape", "scrape-buildjson", "buildjson-ttl", "scrape-markdown", "markdown-ttl"] },
  summary: { nodes: ["start", "validate", "cache-decision", "scrape", "markdown", "summary-store", "summary"], edges: ["start-validate", "validate-cache", "cache-miss-scrape", "scrape-markdown", "markdown-ttl", "ttl-summary"] },
  "invalid-request": { nodes: ["start", "validate", "invalid-request"], edges: ["start-validate", "validate-error"], errorEdges: ["validate-error"] },
  "scrape-failure": { nodes: ["start", "validate", "cache-decision", "scrape", "scrape-failure"], edges: ["start-validate", "validate-cache", "cache-miss-scrape", "scrape-error"], errorEdges: ["scrape-error"] },
  "summary-failure": { nodes: ["start", "validate", "cache-decision", "scrape", "markdown", "summary-store", "summary", "summary-failure"], edges: ["start-validate", "validate-cache", "cache-miss-scrape", "scrape-markdown", "markdown-ttl", "ttl-summary", "summary-error"], errorEdges: ["summary-error"] },
};

const NODE_DETAILS = {
  start: {
    title: "POST /scrape",
    summary: "API entry for a scrape request.",
    inputs: "Request body with a URL.",
    outputs: "Passes control to validation.",
    failures: "Bad payloads can fail before processing.",
    notes: "This begins the request flow.",
  },
  validate: {
    title: "Validate URL",
    summary: "Checks the URL before any fetch.",
    inputs: "User URL.",
    outputs: "Safe HTTPS URL or rejection.",
    failures: "Empty, malformed, or non-HTTPS values.",
    notes: "First guardrail in the flow.",
  },
  "cache-decision": {
    title: "Cache Decision",
    summary: "Checks whether data already exists in cache.",
    inputs: "Validated URL key.",
    outputs: "Cache hit to response or miss to scrape.",
    failures: "A miss changes the path but is not an error.",
    notes: "Redis is checked before new work starts.",
  },
  response: {
    title: "Return JSON",
    summary: "Returns the payload to the client.",
    inputs: "Cached or fresh scrape data.",
    outputs: "Serialized JSON response.",
    failures: "Serialization or shape mismatch.",
    notes: "Main synchronous output step.",
  },
  end: {
    title: "Client Output",
    summary: "The response has left the backend.",
    inputs: "Completed JSON payload.",
    outputs: "Client-visible result.",
    failures: "No further workflow errors here.",
    notes: "Visible end of the request path.",
  },
  scrape: {
    title: "Fetch + Parse",
    summary: "Fetches the page and extracts fields.",
    inputs: "Validated URL and fetch settings.",
    outputs: "HTML-derived metadata.",
    failures: "Timeouts, HTTP errors, non-HTML pages.",
    notes: "Main network step and biggest risk area.",
  },
  "build-json": {
    title: "Build + Cache Result",
    summary: "Builds the response and caches it.",
    inputs: "Parsed page data.",
    outputs: "Cached result ready to return.",
    failures: "Missing fields or schema mismatch.",
    notes: "Stores structured data by URL key.",
  },
  markdown: {
    title: "Create + Cache Markdown",
    summary: "Converts HTML to markdown and stores it.",
    inputs: "Fetched HTML.",
    outputs: "Markdown cached under `markdown:{url}`.",
    failures: "Runs only after scrape succeeds.",
    notes: "Uses the `markdown:{url}` cache key.",
  },
  "summary-store": {
    title: "TTL Cache",
    summary: "Keeps cached outputs with expiry.",
    inputs: "Scrape data, markdown, and future summaries.",
    outputs: "TTL-backed cache entries.",
    failures: "Cache outages or key collisions.",
    notes: "Current keys include `{url}` and `markdown:{url}`.",
  },
  summary: {
    title: "Summarise",
    summary: "Planned stage for generating summaries.",
    inputs: "Cached markdown.",
    outputs: "Future cached summary.",
    failures: "Summariser failure while markdown stays usable.",
    notes: "Expected future key is `summary:{url}`.",
  },
  "invalid-request": {
    title: "Reject Request",
    summary: "Stops the workflow on bad input.",
    inputs: "Unsafe or malformed URL.",
    outputs: "Error response.",
    failures: "This node is itself the failure branch.",
    notes: "No network work should happen after this.",
  },
  "scrape-failure": {
    title: "ScraperError",
    summary: "Fetch or parse failure stops the sync flow.",
    inputs: "Timeouts, HTTP errors, bad content type.",
    outputs: "Error response path.",
    failures: "Captures scrape-stage failures.",
    notes: "A success response is never built after this.",
  },
  "summary-failure": {
    title: "Summary Failed",
    summary: "Summary generation fails after markdown exists.",
    inputs: "Markdown and summariser call.",
    outputs: "Failure branch with reusable markdown.",
    failures: "Model failure or invalid summary output.",
    notes: "Shown separately because scrape data can still be reused.",
  },
};

const RUNS = {
  success: {
    state: "happy",
    nodes: [
      { id: "start", style: "path-happy" },
      { id: "validate", style: "path-happy" },
      { id: "cache-decision", style: "path-happy" },
      { id: "scrape", style: "path-happy" },
      { id: "build-json", style: "path-happy" },
      { id: "response", style: "path-happy" },
      { id: "end", style: "path-happy" },
      { id: "markdown", style: "path-async" },
      { id: "summary-store", style: "path-async" },
      { id: "summary", style: "path-async" },
    ],
    edges: [
      { id: "start-validate", state: "is-running" },
      { id: "validate-cache", state: "is-running" },
      { id: "cache-miss-scrape", state: "is-running" },
      { id: "scrape-buildjson", state: "is-running" },
      { id: "buildjson-response", state: "is-running" },
      { id: "response-end", state: "is-running" },
      { id: "scrape-markdown", state: "is-async" },
      { id: "buildjson-ttl", state: "is-async" },
      { id: "markdown-ttl", state: "is-async" },
      { id: "ttl-summary", state: "is-async" },
      { id: "summary-store", state: "is-async" },
    ],
  },
  error: {
    state: "error",
    nodes: [
      { id: "start", style: "path-happy" },
      { id: "validate", style: "path-happy" },
      { id: "cache-decision", style: "path-happy" },
      { id: "scrape", style: "path-error" },
      { id: "scrape-failure", style: "path-error" },
    ],
    edges: [
      { id: "start-validate", state: "is-running" },
      { id: "validate-cache", state: "is-running" },
      { id: "cache-miss-scrape", state: "is-running" },
      { id: "scrape-error", state: "is-error" },
    ],
  },
};

let timers = [];
let selectedNodeId = null;
const edgePaths = new Map();
const edgeDots = new Map();

function getNode(nodeId) {
  return document.querySelector(`.node[data-node="${nodeId}"]`);
}

function getRect(node) {
  return {
    x: node.offsetLeft,
    y: node.offsetTop,
    width: node.offsetWidth,
    height: node.offsetHeight,
  };
}

function getAnchor(nodeId, side) {
  const node = getNode(nodeId);
  if (!node) return { x: 0, y: 0 };

  const rect = getRect(node);
  const isDecision = node.classList.contains("decision");
  const inset = 2;

  if (isDecision) {
    const midX = rect.x + rect.width / 2;
    const midY = rect.y + rect.height / 2;
    if (side === "top") return { x: midX, y: rect.y + inset };
    if (side === "bottom") return { x: midX, y: rect.y + rect.height - inset };
    if (side === "left") return { x: rect.x + inset, y: midY };
    return { x: rect.x + rect.width - inset, y: midY };
  }

  if (side === "top") return { x: rect.x + rect.width / 2, y: rect.y + inset };
  if (side === "bottom") return { x: rect.x + rect.width / 2, y: rect.y + rect.height - inset };
  if (side === "left") return { x: rect.x + inset, y: rect.y + rect.height / 2 };
  return { x: rect.x + rect.width - inset, y: rect.y + rect.height / 2 };
}

function createPath(from, to, route) {
  if (route === "horizontal") {
    const start = getAnchor(from, "right");
    const end = getAnchor(to, "left");
    const bend = Math.max(18, (end.x - start.x) * 0.42);
    return `M ${start.x} ${start.y} C ${start.x + bend} ${start.y}, ${end.x - bend} ${end.y}, ${end.x} ${end.y}`;
  }

  if (route === "vertical") {
    const start = getAnchor(from, "bottom");
    const end = getAnchor(to, "top");
    const bend = Math.max(26, (end.y - start.y) * 0.42);
    return `M ${start.x} ${start.y} C ${start.x} ${start.y + bend}, ${end.x} ${end.y - bend}, ${end.x} ${end.y}`;
  }

  if (route === "vertical-up") {
    const start = getAnchor(from, "top");
    const end = getAnchor(to, "bottom");
    const bend = Math.max(26, (start.y - end.y) * 0.42);
    return `M ${start.x} ${start.y} C ${start.x} ${start.y - bend}, ${end.x} ${end.y + bend}, ${end.x} ${end.y}`;
  }

  if (route === "curve-down-left") {
    const start = getAnchor(from, "bottom");
    const end = getAnchor(to, "top");
    const midY = start.y + 34;
    return `M ${start.x} ${start.y} C ${start.x} ${midY}, ${end.x + 54} ${end.y - 36}, ${end.x} ${end.y}`;
  }

  if (route === "curve-down") {
    const start = getAnchor(from, "bottom");
    const end = getAnchor(to, "top");
    const midY = start.y + 36;
    return `M ${start.x} ${start.y} C ${start.x} ${midY}, ${end.x - 12} ${end.y - 40}, ${end.x} ${end.y}`;
  }

  if (route === "curve-back") {
    const start = getAnchor(from, "bottom");
    const end = getAnchor(to, "top");
    return `M ${start.x} ${start.y} C ${start.x - 24} ${start.y + 34}, ${end.x + 18} ${end.y + 42}, ${end.x} ${end.y}`;
  }

  return createPath(from, to, "horizontal");
}

function createEdgePath(id, type) {
  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("id", `edge-${id}`);
  path.setAttribute("class", `edge-path ${type}`);
  path.setAttribute("marker-end", "url(#arrow-idle)");
  edgeLayer.appendChild(path);
  edgePaths.set(id, path);

  const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  dot.setAttribute("class", "edge-overlay-dot");
  dot.setAttribute("r", "5");
  dotLayer.appendChild(dot);
  edgeDots.set(id, dot);
}

function renderEdges() {
  if (!diagramCanvas) return;

  edgePaths.forEach((path, edgeId) => {
    const config = EDGE_CONFIG[edgeId];
    if (!config) return;
    const d = createPath(config.from, config.to, config.route);
    path.setAttribute("d", d);
  });
}

function setInspector(nodeId, options = {}) {
  const { applyFocus = false } = options;
  const data = NODE_DETAILS[nodeId];
  if (!data) return;

  diagramCanvas.classList.toggle("node-focus", applyFocus);

  nodeButtons.forEach((node) => {
    const isCurrent = node.dataset.node === nodeId;
    const isOnPath = applyFocus && NODE_PATHS[nodeId]?.nodes.includes(node.dataset.node);
    node.classList.toggle("active", isCurrent);
    node.classList.toggle("path-visible", isOnPath);
  });

  edgePaths.forEach((edge, edgeId) => {
    const pathDef = NODE_PATHS[nodeId];
    const isVisible = applyFocus && pathDef?.edges.includes(edgeId);
    const isError = applyFocus && pathDef?.errorEdges?.includes(edgeId);
    edge.classList.toggle("path-visible", Boolean(isVisible));
    edge.classList.toggle("idle-highlight", Boolean(isVisible && !isError));
    if (!applyFocus) {
      edge.classList.remove("path-visible", "idle-highlight");
    }
  });

  detailTitle.textContent = data.title;
  detailSummary.textContent = data.summary;
  detailInputs.textContent = data.inputs;
  detailOutputs.textContent = data.outputs;
  detailFailures.textContent = data.failures;
  detailNotes.textContent = data.notes;
}

function clearRunState() {
  timers.forEach((timer) => {
    window.clearTimeout(timer);
    window.cancelAnimationFrame(timer);
  });
  timers = [];

  nodeButtons.forEach((node) => {
    node.classList.remove("path-happy", "path-error", "path-async", "is-running", "is-complete");
  });

  edgePaths.forEach((edge) => {
    edge.classList.remove("is-running", "is-complete", "is-error", "is-async");
  });

  edgeDots.forEach((dot) => {
    dot.classList.remove("is-running", "is-error", "is-async");
    dot.setAttribute("cx", "0");
    dot.setAttribute("cy", "0");
  });

  pathState.className = "path-state";
  pathState.textContent = "idle";
}

function moveDot(pathId) {
  const path = edgePaths.get(pathId);
  const dot = edgeDots.get(pathId);
  if (!path || !dot) return;

  const length = path.getTotalLength();
  let progress = 0;

  function step() {
    progress += 0.026;
    const point = path.getPointAtLength(Math.min(progress, 1) * length);
    dot.setAttribute("cx", point.x.toFixed(2));
    dot.setAttribute("cy", point.y.toFixed(2));
    if (progress < 1) {
      const raf = window.requestAnimationFrame(step);
      timers.push(raf);
    }
  }

  step();
}

function animateRun(runKey) {
  const run = RUNS[runKey];
  if (!run) return;

  clearRunState();
  pathState.className = `path-state ${run.state}`;
  pathState.textContent = run.state === "happy" ? "happy path" : "failure path";

  run.nodes.forEach((nodeStep, index) => {
    const timer = window.setTimeout(() => {
      const node = getNode(nodeStep.id);
      if (!node) return;

      const runningNode = document.querySelector(".node.is-running");
      if (runningNode) {
        runningNode.classList.remove("is-running");
        if (!runningNode.classList.contains("path-error")) {
          runningNode.classList.add("is-complete");
        }
      }

      node.classList.remove("is-complete");
      node.classList.add(nodeStep.style, "is-running");
      setInspector(nodeStep.id, { applyFocus: false });
    }, index * 520);
    timers.push(timer);
  });

  run.edges.forEach((edgeStep, index) => {
    const timer = window.setTimeout(() => {
      const edge = edgePaths.get(edgeStep.id);
      const dot = edgeDots.get(edgeStep.id);
      if (!edge || !dot) return;

      const runningEdge = document.querySelector(".edge-path.is-running");
      if (runningEdge) {
        runningEdge.classList.remove("is-running");
        runningEdge.classList.add("is-complete");
      }

      edge.classList.remove("is-running", "is-complete", "is-error", "is-async");
      dot.classList.remove("is-running", "is-error", "is-async");

      edge.classList.add(edgeStep.state);
      dot.classList.add(edgeStep.state);
      moveDot(edgeStep.id);
    }, index * 520 + 180);
    timers.push(timer);
  });
}

function clearSelection() {
  selectedNodeId = null;
  diagramCanvas.classList.remove("node-focus");
  nodeButtons.forEach((node) => {
    node.classList.remove("active", "path-visible");
  });
  edgePaths.forEach((edge) => {
    edge.classList.remove("path-visible", "idle-highlight");
  });
}

nodeButtons.forEach((node) => {
  node.addEventListener("click", () => {
    const nodeId = node.dataset.node;
    if (selectedNodeId === nodeId) {
      clearSelection();
      setInspector(nodeId, { applyFocus: false });
      return;
    }

    selectedNodeId = nodeId;
    setInspector(nodeId, { applyFocus: true });
  });
});

runSuccessButton?.addEventListener("click", () => {
  clearSelection();
  animateRun("success");
});

runErrorButton?.addEventListener("click", () => {
  clearSelection();
  animateRun("error");
});

resetButton?.addEventListener("click", () => {
  clearRunState();
  clearSelection();
  setInspector("start", { applyFocus: false });
});

Object.entries(EDGE_CONFIG).forEach(([id, config]) => createEdgePath(id, config.type));
renderEdges();
window.addEventListener("resize", renderEdges);
window.addEventListener("load", renderEdges);
setInspector("start", { applyFocus: false });
