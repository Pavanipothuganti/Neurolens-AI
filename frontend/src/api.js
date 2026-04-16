const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "http://127.0.0.1:8000";

const parseError = async (response) => {
  try {
    const contentType = response.headers.get("content-type") || "";

    if (contentType.includes("application/json")) {
      const payload = await response.json();
      return payload.detail || payload.message || `Request failed with status ${response.status}.`;
    }

    const text = await response.text();
    if (text.trim()) {
      return `${response.status} ${response.statusText}: ${text.slice(0, 180)}`;
    }

    return `Request failed with status ${response.status}.`;
  } catch {
    return `Request failed with status ${response.status}.`;
  }
};

const createFormData = (file) => {
  const formData = new FormData();
  formData.append("file", file);
  return formData;
};

const getAuthHeaders = () => {
  const token = localStorage.getItem("neurolens_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const login = async (username, password) => {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password, email: "dummy@dummy.com" }), // Backend UserCreate needs email
  });
  if (!response.ok) throw new Error(await parseError(response));
  const data = await response.json();
  localStorage.setItem("neurolens_token", data.access_token);
  localStorage.setItem("neurolens_user", JSON.stringify(data.user));
  return data;
};

export const signup = async (username, email, password) => {
  const response = await fetch(`${API_BASE_URL}/api/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, email, password }),
  });
  if (!response.ok) throw new Error(await parseError(response));
  const data = await response.json();
  localStorage.setItem("neurolens_token", data.access_token);
  localStorage.setItem("neurolens_user", JSON.stringify(data.user));
  return data;
};

export const logout = () => {
  localStorage.removeItem("neurolens_token");
  localStorage.removeItem("neurolens_user");
};

export const getPrediction = async (file) => {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api/predict`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: createFormData(file),
    });
  } catch {
    throw new Error(
      `Cannot connect to the backend at ${API_BASE_URL}. Start the FastAPI server and try again.`
    );
  }

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return response.json();
};

export const getGradCamExplanation = async (file, overlayOpacity) => {
  const params = new URLSearchParams({
    overlay_opacity: overlayOpacity.toString(),
  });

  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api/explanations/gradcam?${params}`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: createFormData(file),
    });
  } catch {
    throw new Error(
      `Cannot connect to the backend at ${API_BASE_URL}. Start the FastAPI server and try again.`
    );
  }

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return response.json();
};

export const getLimeExplanation = async (file, numSamples) => {
  const params = new URLSearchParams({
    num_samples: numSamples.toString(),
  });

  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api/explanations/lime?${params}`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: createFormData(file),
    });
  } catch {
    throw new Error(
      `Cannot connect to the backend at ${API_BASE_URL}. Start the FastAPI server and try again.`
    );
  }

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return response.json();
};

export const getAnalysisHistory = async () => {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api/analyses`, {
      headers: getAuthHeaders(),
    });
  } catch {
    throw new Error(
      `Cannot connect to the backend at ${API_BASE_URL}. Start the FastAPI server and try again.`
    );
  }

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return response.json();
};

export const getAnalysisById = async (analysisId) => {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api/analyses/${analysisId}`, {
      headers: getAuthHeaders(),
    });
  } catch {
    throw new Error(
      `Cannot connect to the backend at ${API_BASE_URL}. Start the FastAPI server and try again.`
    );
  }

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return response.json();
};

export const downloadPdfReport = async (analysisId, explanations = {}) => {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api/reports/pdf`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify({
        analysis_id: analysisId,
        gradcam_base64: explanations.gradcam || null,
        lime_base64: explanations.lime || null,
      }),
    });
  } catch {
    throw new Error(
      `Cannot connect to the backend at ${API_BASE_URL}. Start the FastAPI server and try again.`
    );
  }

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return response.blob();
};
