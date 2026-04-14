const form = document.querySelector("#scrape-form");
const urlInput = document.querySelector("#url-input");
const submitButton = document.querySelector("#submit-button");
const downloadButton = document.querySelector("#download-button");
const statusCard = document.querySelector("#status-card");
const previewCode = document.querySelector("#preview-code");
const previewTitle = document.querySelector("#preview-title");
const previewDescription = document.querySelector("#preview-description");
const previewMetrics = document.querySelector("#preview-metrics");
const previewMeta = document.querySelector("#preview-meta");
const scrapedDataScroll = document.querySelector("#scraped-data-scroll");
const docsLink = document.querySelector("#docs-link");

function resolveApiBase() {
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

if (docsLink) {
  docsLink.href = `${API_BASE}/docs`;
}

function setStatus(state, title, message) {
  statusCard.innerHTML = `
    <div class="status-pill ${state}">${state}</div>
    <p class="status-title">${title}</p>
    <p class="status-message">${message}</p>
  `;
}

function setPreviewEmpty() {
  previewCode.textContent = "No result yet";
  previewTitle.textContent = "Scrape preview will appear here";
  previewDescription.textContent =
    "Preview a page to inspect the title, metadata, and content summary before downloading markdown.";
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
    <p><span>Resolved URL</span> Preview not available yet.</p>
    <p><span>Status</span> Waiting for input.</p>
    <p><span>Content Length</span> 0 bytes</p>
  `;
  scrapedDataScroll.innerHTML = `
    <div class="data-group">
      <h3>Awaiting scrape</h3>
      <p>The scraped data feed will stay here after previewing a URL.</p>
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
        <li>Preview a page to populate this block.</li>
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

  return items
    .map((item) => `<li>${item}</li>`)
    .join("");
}

function renderPreview(result) {
  const { short_code: shortCode, data } = result;
  previewCode.textContent = shortCode;
  previewTitle.textContent = data.title || "Untitled page";
  previewDescription.textContent =
    data.meta_description || "No meta description was found for this page.";
  previewMetrics.innerHTML = `
    <article class="metric">
      <span>Links</span>
      <strong>${data.links.length}</strong>
    </article>
    <article class="metric">
      <span>Images</span>
      <strong>${data.images.length}</strong>
    </article>
    <article class="metric">
      <span>Headings</span>
      <strong>${data.headings.length}</strong>
    </article>
  `;
  previewMeta.innerHTML = `
    <p><span>Resolved URL</span> ${data.url}</p>
    <p><span>Status</span> ${data.status_code}</p>
    <p><span>Content Length</span> ${data.content_length.toLocaleString()} bytes</p>
  `;
  scrapedDataScroll.innerHTML = `
    <div class="data-group">
      <h3>${data.title || "Untitled page"}</h3>
      <p>Short code: ${shortCode}</p>
    </div>
    <div class="data-group">
      <h4>Meta Description</h4>
      <p>${data.meta_description || "No meta description was found for this page."}</p>
    </div>
    <div class="data-group">
      <h4>Resolved URL</h4>
      <p>${data.url}</p>
    </div>
    <div class="data-group">
      <h4>Headings</h4>
      <ul class="data-list">
        ${renderList(data.headings, "No headings were extracted.")}
      </ul>
    </div>
    <div class="data-group">
      <h4>Links</h4>
      <ul class="data-list">
        ${renderList(data.links, "No links were extracted.")}
      </ul>
    </div>
    <div class="data-group">
      <h4>Images</h4>
      <ul class="data-list">
        ${renderList(data.images, "No image sources were extracted.")}
      </ul>
    </div>
  `;
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

async function fetchPreview(url) {
  const response = await fetch(`${API_BASE}/scrape`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ url }),
  });

  if (!response.ok) {
    throw new Error(await parseError(response, "Unable to preview this URL."));
  }

  return response.json();
}

async function downloadMarkdown(url) {
  const response = await fetch(`${API_BASE}/scrape/markdown`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ url }),
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

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const url = urlInput.value.trim();
  if (!url) {
    setStatus("error", "URL required", "Add an HTTPS URL before starting the scraper.");
    urlInput.focus();
    return;
  }

  submitButton.disabled = true;
  downloadButton.disabled = true;
  currentPreviewUrl = "";
  setStatus("loading", "Building preview", "Fetching the page and inspecting the content so you can review it first.");

  try {
    const result = await fetchPreview(url);
    currentPreviewUrl = url;
    renderPreview(result);
    downloadButton.disabled = false;
    setStatus("success", "Preview ready", "Review the scrape result below. Download markdown only if it looks right.");
  } catch (error) {
    setPreviewEmpty();
    const message = error instanceof Error ? error.message : "Something went wrong while previewing the page.";
    setStatus("error", "Preview failed", message);
  } finally {
    submitButton.disabled = false;
  }
});

downloadButton.addEventListener("click", async () => {
  if (!currentPreviewUrl) {
    setStatus("error", "Preview first", "Preview a valid URL before downloading markdown.");
    return;
  }

  downloadButton.disabled = true;
  submitButton.disabled = true;
  setStatus("loading", "Preparing download", "Converting the page to markdown and packaging your file.");

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
