const form = document.querySelector("#analysis-form");
const transcriptInput = document.querySelector("#transcript");
const fileInput = document.querySelector("#transcript-file");
const submitButton = document.querySelector("#submit-button");
const errorElement = document.querySelector("#error");
const progressElement = document.querySelector("#progress");
const reportElement = document.querySelector("#report");
const characterCount = document.querySelector("#char-count");

transcriptInput.addEventListener("input", () => {
  transcriptInput.dataset.format = "text";
  characterCount.textContent = `${transcriptInput.value.length.toLocaleString()} / 100,000`;
});

fileInput.addEventListener("change", async () => {
  const file = fileInput.files[0];
  if (!file) return;
  if (file.size > 1_000_000) {
    showError("Transcript file must be 1 MB or smaller.");
    fileInput.value = "";
    return;
  }
  try {
    transcriptInput.value = await file.text();
    characterCount.textContent = `${transcriptInput.value.length.toLocaleString()} / 100,000`;
    transcriptInput.dataset.format = file.name.toLowerCase().endsWith(".vtt") ? "vtt" : "text";
    showError("");
  } catch {
    showError("The selected file could not be read.");
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const transcript = transcriptInput.value.trim();
  if (!transcript) {
    showError("Paste transcript text or select a transcript file first.");
    return;
  }

  const format = transcriptInput.dataset.format || "text";
  submitButton.disabled = true;
  progressElement.textContent = "Analyzing transcript cues…";
  reportElement.hidden = true;
  showError("");

  try {
    const response = await fetch("/api/analyses", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transcript, transcript_format: format }),
    });
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.detail || "The transcript could not be analyzed.");
    }
    renderReport(result);
    progressElement.textContent = "Review complete.";
  } catch (error) {
    showError(error.message || "The request failed. Please try again.");
    progressElement.textContent = "";
  } finally {
    submitButton.disabled = false;
  }
});

function showError(message) {
  errorElement.textContent = message;
  errorElement.hidden = !message;
}

function renderReport(report) {
  reportElement.replaceChildren();
  reportElement.append(
    heading("Your review"),
    paragraph(report.summary, "notice"),
    paragraph("Overall category: Not assessed in this stage", "rating"),
    paragraph(
      `Exact phrase cues found in ${report.evidence_coverage.dimensions_with_cues} of `
        + `${report.evidence_coverage.total_dimensions} dimensions. This is not a confidence score.`,
      "coverage",
    ),
  );

  const dimensionTitle = heading("Dimensions");
  reportElement.append(dimensionTitle);
  const dimensionList = document.createElement("div");
  dimensionList.className = "dimension-grid";
  for (const dimension of report.dimensions) {
    const card = document.createElement("article");
    card.className = "dimension card";
    card.append(
      heading(dimension.name, "h3"),
      paragraph(
        dimension.status === "cues_found"
          ? `Transcript cues: ${dimension.evidence_pattern.replaceAll("_", " ")}`
          : "No matching cue found",
        "score",
      ),
      paragraph(dimension.rationale, "muted"),
    );
    dimensionList.append(card);
  }
  reportElement.append(dimensionList, heading("Evidence and recommendations"));

  if (report.observations.length === 0) {
    reportElement.append(paragraph("No explicit rubric phrases were found in the transcript.", "notice"));
  }
  for (const observation of report.observations) {
    const card = document.createElement("article");
    card.className = "card observation";
    const timestamp = observation.start_seconds === null
      ? observation.segment_id
      : `${formatTimestamp(observation.start_seconds)} (${observation.segment_id})`;
    card.append(
      heading(observation.observation, "h3"),
      paragraph(`Evidence · ${timestamp}: “${observation.excerpt}”`, "quote"),
      paragraph(observation.interpretation, "muted"),
    );
    if (observation.recommendation) {
      card.append(paragraph(`Try: ${observation.recommendation}`, "recommendation"));
    }
    reportElement.append(card);
  }

  reportElement.append(heading("Limitations"));
  const limitations = document.createElement("ul");
  for (const limitation of report.limitations) {
    const item = document.createElement("li");
    item.textContent = limitation;
    limitations.append(item);
  }
  reportElement.append(limitations);
  reportElement.hidden = false;
}

function heading(text, tag = "h2") {
  const element = document.createElement(tag);
  element.textContent = text;
  return element;
}

function paragraph(text, className = "") {
  const element = document.createElement("p");
  element.className = className;
  element.textContent = text;
  return element;
}

function formatTimestamp(seconds) {
  const wholeSeconds = Math.floor(seconds);
  const hours = Math.floor(wholeSeconds / 3600);
  const minutes = Math.floor((wholeSeconds % 3600) / 60);
  const remainder = wholeSeconds % 60;
  return hours
    ? `${hours}:${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`
    : `${minutes}:${String(remainder).padStart(2, "0")}`;
}
