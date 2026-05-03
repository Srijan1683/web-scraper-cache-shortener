const form = document.querySelector("#scrape-form");
const urlInput = document.querySelector("#url-input");
const summaryTypeSelect = document.querySelector("#summary-type");
const submitButton = document.querySelector("#submit-button");
const downloadButton = document.querySelector("#download-button");
const statusCard = document.querySelector("#status-card");
const previewCode = document.querySelector("#preview-code");
const previewTitle = document.querySelector("#preview-title");
const previewDescription = document.querySelector("#preview-description");
const previewMetrics = document.querySelector("#preview-metrics");
const previewMeta = document.querySelector("#preview-meta");
const scrapedDataScroll = document.querySelector("#scraped-data-scroll");
const summaryModeBadge = document.querySelector("#summary-mode-badge");
const summaryHeading = document.querySelector("#summary-heading");
const summaryBody = document.querySelector("#summary-body");
const summaryMeta = document.querySelector("#summary-meta");
const docsLink = document.querySelector("#docs-link");

function resolveApiBase() {
  const isLocalHost =
    window.location.hostname === "127.0.0.1" ||
    window.location.hostname === "localhost";

  if (isLocalHost) {
    return window.location.origin;
  }

  const configuredBase = window.WEB_SCRAPER_CONFIG?.apiBaseUrl?.trim();
  if (configuredBase) {
    return configuredBase.replace(/\/+$/, "");
  }

  if (window.location.protocol === "file:") {
    return "http://127.0.0.1:8000";
  }

  return window.location.origin;
}

const API_BASE = resolveApiBase();

let currentPreviewUrl = "";
let currentJobId = "";
let currentSummaryType = "brief";

if (docsLink) {
  docsLink.href = `${API_BASE}/docs`;
}

function wait(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function formatSummaryType(summaryType) {
  return summaryType === "detailed" ? "Detailed" : "Brief";
}

function formatJobStatus(status) {
  if (status === "crawling") {
    return "scraping";
  }

  return status;
}

function setStatus(state, title, message) {
  statusCard.innerHTML = `
    <div class="status-pill ${state}">${state}</div>
    <p class="status-title">${title}</p>
    <p class="status-message">${message}</p>
  `;
}

function setSummaryEmpty(summaryType = "brief") {
  summaryModeBadge.textContent = formatSummaryType(summaryType);
  summaryHeading.textContent = "AI summary will appear here";
  summaryBody.textContent = "Choose a summary mode and run the scrape job to populate this section.";
  summaryMeta.innerHTML = `
    <p><span>Model</span> Waiting for summary.</p>
    <p><span>Prompt Tokens</span> 0</p>
    <p><span>Completion Tokens</span> 0</p>
    <p><span>Total Tokens</span> 0</p>
  `;
}

function setPreviewEmpty() {
  previewCode.textContent = "No result yet";
  previewTitle.textContent = "Scrape preview will appear here";
  previewDescription.textContent =
    "Run a scrape job to inspect page metadata and summary output before downloading markdown.";
  previewMetrics.innerHTML = `
    <article class="metric">
      <span>Links</span>
      <strong>0</strong>
    </article>
    <article class="metric">
      <span>Images</span>
      <strong>0</strong>
    </article>
    <article class="metric">
      <span>Headings</span>
      <strong>0</strong>
    </article>
  `;
  previewMeta.innerHTML = `
    <p><span>Job</span> No job submitted yet.</p>
    <p><span>Status</span> Waiting for input.</p>
    <p><span>Resolved URL</span> Preview not available yet.</p>
    <p><span>Content Length</span> 0 bytes</p>
  `;
  scrapedDataScroll.innerHTML = `
    <div class="data-group">
      <h3>Awaiting scrape</h3>
      <p>The scraped data feed will stay here after the job completes.</p>
    </div>
    <div class="data-group">
      <h4>Title</h4>
      <p>No data yet.</p>
    </div>
    <div class="data-group">
      <h4>Meta Description</h4>
      <p>No data yet.</p>
    </div>
    <div class="data-group">
      <h4>Headings</h4>
      <ul class="data-list">
        <li>Run a scrape job to populate this block.</li>
      </ul>
    </div>
    <div class="data-group">
      <h4>Links</h4>
      <ul class="data-list">
        <li>Scraped links will appear here.</li>
      </ul>
    </div>
    <div class="data-group">
      <h4>Images</h4>
      <ul class="data-list">
        <li>Scraped image sources will appear here.</li>
      </ul>
    </div>
  `;
}

function renderList(items, emptyMessage) {
  if (!items.length) {
    return `<li>${emptyMessage}</li>`;
  }

  return items.map((item) => `<li>${item}</li>`).join("");
}

function resolveResultPayload(job) {
  if (job?.result?.data) {
    return job.result;
  }

  if (job?.data) {
    return job;
  }

  return null;
}

function renderSummary(job) {
  const jobStatus = formatJobStatus(job.status);
  summaryModeBadge.textContent = formatSummaryType(job.summary_type);

  if (!job.summary) {
    summaryHeading.textContent = "Summary in progress";
    summaryBody.textContent =
      job.status === "failed"
        ? job.error || "The scrape job failed before a summary could be generated."
        : `The backend is still ${jobStatus}. The summary will appear once the job completes.`;
    summaryMeta.innerHTML = `
      <p><span>Model</span> Not available yet.</p>
      <p><span>Prompt Tokens</span> 0</p>
      <p><span>Completion Tokens</span> 0</p>
      <p><span>Total Tokens</span> 0</p>
    `;
    return;
  }

  const { model, token_usage: tokenUsage } = job.summary;
  summaryHeading.textContent = `${formatSummaryType(job.summary_type)} summary`;
  summaryBody.textContent = job.summary.summary;
  summaryMeta.innerHTML = `
    <p><span>Model</span> ${model}</p>
    <p><span>Prompt Tokens</span> ${tokenUsage.prompt_tokens.toLocaleString()}</p>
    <p><span>Completion Tokens</span> ${tokenUsage.completion_tokens.toLocaleString()}</p>
    <p><span>Total Tokens</span> ${tokenUsage.total_tokens.toLocaleString()}</p>
  `;
}

function renderPreview(job) {
  const resultPayload = resolveResultPayload(job);

  if (!resultPayload) {
    previewCode.textContent = job.job_id;
    previewTitle.textContent = "Job accepted";
    previewDescription.textContent =
      "The backend has accepted the scrape job. Preview data will appear as soon as the scrape result is available.";
    previewMetrics.innerHTML = `
      <article class="metric">
        <span>Links</span>
        <strong>0</strong>
      </article>
      <article class="metric">
        <span>Images</span>
        <strong>0</strong>
      </article>
      <article class="metric">
        <span>Headings</span>
        <strong>0</strong>
      </article>
    `;
    previewMeta.innerHTML = `
      <p><span>Job</span> ${job.job_id}</p>
      <p><span>Status</span> ${formatJobStatus(job.status)}</p>
      <p><span>Resolved URL</span> ${job.original_url}</p>
      <p><span>Content Length</span> Waiting for scrape result.</p>
    `;
    return;
  }

  const shortCode = resultPayload.short_code || job.short_code || job.job_id || "Pending";
  const data = resultPayload.data || null;
  if (!data) {
    previewCode.textContent = job.job_id || "Pending";
    previewTitle.textContent = "Result shape incomplete";
    previewDescription.textContent =
      "The backend returned a scrape result without the expected page data block.";
    previewMeta.innerHTML = `
      <p><span>Job</span> ${job.job_id || "Unavailable"}</p>
      <p><span>Status</span> ${formatJobStatus(job.status || "queued")}</p>
      <p><span>Resolved URL</span> ${job.original_url || "Unavailable"}</p>
      <p><span>Content Length</span> Unavailable</p>
    `;
    return;
  }

  previewCode.textContent = shortCode;
  previewTitle.textContent = data?.title || "Untitled page";
  previewDescription.textContent =
    data?.meta_description || "No meta description was found for this page.";
  previewMetrics.innerHTML = `
    <article class="metric">
      <span>Links</span>
      <strong>${(data?.links || []).length}</strong>
    </article>
    <article class="metric">
      <span>Images</span>
      <strong>${(data?.images || []).length}</strong>
    </article>
    <article class="metric">
      <span>Headings</span>
      <strong>${(data?.headings || []).length}</strong>
    </article>
  `;
  previewMeta.innerHTML = `
    <p><span>Job</span> ${job.job_id}</p>
    <p><span>Status</span> ${formatJobStatus(job.status)}</p>
    <p><span>Resolved URL</span> ${data?.url || job.original_url || "Unavailable"}</p>
    <p><span>Content Length</span> ${(data?.content_length || 0).toLocaleString()} bytes</p>
  `;
  scrapedDataScroll.innerHTML = `
    <div class="data-group">
      <h3>${data?.title || "Untitled page"}</h3>
      <p>Short code: ${shortCode}</p>
    </div>
    <div class="data-group">
      <h4>Meta Description</h4>
      <p>${data?.meta_description || "No meta description was found for this page."}</p>
    </div>
    <div class="data-group">
      <h4>Resolved URL</h4>
      <p>${data?.url || job.original_url || "Unavailable"}</p>
    </div>
    <div class="data-group">
      <h4>Headings</h4>
      <ul class="data-list">
        ${renderList(data?.headings || [], "No headings were extracted.")}
      </ul>
    </div>
    <div class="data-group">
      <h4>Links</h4>
      <ul class="data-list">
        ${renderList(data?.links || [], "No links were extracted.")}
      </ul>
    </div>
    <div class="data-group">
      <h4>Images</h4>
      <ul class="data-list">
        ${renderList(data?.images || [], "No image sources were extracted.")}
      </ul>
    </div>
  `;
}

function renderJob(job) {
  renderPreview(job);
  renderSummary(job);
}

async function parseError(response, fallbackMessage) {
  let message = fallbackMessage;

  try {
    const errorData = await response.json();
    if (errorData && typeof errorData.detail === "string") {
      message = errorData.detail;
    }
  } catch (error) {
    message = fallbackMessage;
  }

  return message;
}

async function submitScrapeJob(url, summaryType) {
  const response = await fetch(`${API_BASE}/scrape`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ url, summary_type: summaryType })
  });

  if (!response.ok) {
    throw new Error(await parseError(response, "Unable to start this scrape job."));
  }

  return response.json();
}

async function fetchJob(jobId) {
  const response = await fetch(`${API_BASE}/scrape/${jobId}`);

  if (!response.ok) {
    throw new Error(await parseError(response, "Unable to fetch the scrape job status."));
  }

  return response.json();
}

async function downloadMarkdown(url) {
  const response = await fetch(`${API_BASE}/scrape/markdown`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ url })
  });

  if (!response.ok) {
    throw new Error(await parseError(response, "Unable to generate markdown for this URL."));
  }

  const blob = await response.blob();
  const contentDisposition = response.headers.get("Content-Disposition") || "";
  const fileNameMatch = contentDisposition.match(/filename="([^"]+)"/i);
  const fileName = fileNameMatch ? fileNameMatch[1] : "scraped-page.md";

  const objectUrl = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(objectUrl);

  return fileName;
}

async function waitForJobCompletion(jobId) {
  const maxAttempts = 35;

  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    const job = await fetchJob(jobId);
    renderJob(job);

    if (job.status === "completed") {
      return job;
    }

    if (job.status === "failed") {
      throw new Error(job.error || "The scrape job failed.");
    }

    const stage = formatJobStatus(job.status);
    setStatus("loading", `Job ${stage}`, `The backend is currently ${stage}. Summary generation will appear automatically when the job completes.`);
    await wait(1200);
  }

  throw new Error("The scrape job took too long to finish. Try again in a moment.");
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const url = urlInput.value.trim();
  const summaryType = summaryTypeSelect.value;

  if (!url) {
    setStatus("error", "URL required", "Add an HTTPS URL before starting the scraper.");
    urlInput.focus();
    return;
  }

  submitButton.disabled = true;
  downloadButton.disabled = true;
  currentPreviewUrl = url;
  currentJobId = "";
  currentSummaryType = summaryType;
  setSummaryEmpty(summaryType);
  setStatus("loading", "Starting job", "Submitting the scrape job and checking whether the result can be reused from cache.");

  try {
    const initialJob = await submitScrapeJob(url, summaryType);
    currentJobId = initialJob.job_id;
    renderJob(initialJob);

    if (initialJob.status === "completed") {
      downloadButton.disabled = false;
      setStatus("success", "Job complete", "The scrape, summary, and cached preview are ready to inspect.");
      return;
    }

    const completedJob = await waitForJobCompletion(initialJob.job_id);
    currentJobId = completedJob.job_id;
    currentPreviewUrl = url;
    downloadButton.disabled = false;
    setStatus("success", "Job complete", "The scrape result and AI summary are ready. Download markdown if you want the source file.");
  } catch (error) {
    const message = error instanceof Error ? error.message : "Something went wrong while running the scrape job.";
    setStatus("error", "Job failed", message);
  } finally {
    submitButton.disabled = false;
  }
});

downloadButton.addEventListener("click", async () => {
  if (!currentPreviewUrl) {
    setStatus("error", "Scrape first", "Run a scrape job before downloading markdown.");
    return;
  }

  downloadButton.disabled = true;
  submitButton.disabled = true;
  setStatus("loading", "Preparing download", "Retrieving markdown for the current URL and packaging your file.");

  try {
    const fileName = await downloadMarkdown(currentPreviewUrl);
    setStatus("success", "Download complete", `${fileName} was generated and downloaded successfully.`);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Something went wrong while downloading markdown.";
    setStatus("error", "Download failed", message);
  } finally {
    downloadButton.disabled = false;
    submitButton.disabled = false;
  }
});

setPreviewEmpty();
setSummaryEmpty(currentSummaryType);
