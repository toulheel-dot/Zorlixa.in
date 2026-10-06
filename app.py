export default async function handler(request, response) {
  const startTime = Date.now();
  const query = request.query.query;
  const apikey = request.query.key;

  // 🔑 Key check
  if (!apikey) {
    return response.status(401).json({ 
      message: "Provide correct key",
      contact: "@dmforbans"
    });
  }

  const VALID_KEYS = {
    "KKK638663l": { expires: 1830902400000 }
  };

  const keyInfo = VALID_KEYS[apikey];

  if (!keyInfo) {
    return response.status(403).json({ 
      message: "Provide correct key",
      contact: "@dmforbans"
    });
  }

  const now = Date.now();
  if (now > keyInfo.expires) {
    const expiryDate = new Date(keyInfo.expires).toISOString().split("T")[0];
    return response.status(403).json({ 
      message: "Your API key expired",
      expired_on: expiryDate,
      contact: "@dmforbans"
    });
  }

  const expiryDate = new Date(keyInfo.expires).toISOString().split("T")[0];

  // 🔢 Counter — Upstash Redis से
  let totalCalls = 0;
  try {
    const incrRes = await fetch(`${process.env.UPSTASH_URL}/incr/total_calls`, {
      headers: {
        Authorization: `Bearer ${process.env.UPSTASH_TOKEN}`
      }
    });
    const incrData = await incrRes.json();
    totalCalls = incrData.result || 1;
  } catch (e) {
    totalCalls = 0;
  }

  if (!query) {
    return response.status(400).json({ 
      message: "Provide query parameter",
      contact: "@dmforbans"
    });
  }

  const apiUrl = `https://x-trace-x-traceowner-high-tech-num.vercel.app/api/search?key=@x_TRACEOWNER&query=${encodeURIComponent(query)}`;

  try {
    const apiResponse = await fetch(apiUrl);

    const responseTimeMs = Date.now() - startTime;
    const responseTimeSec = (responseTimeMs / 1000).toFixed(3);

    if (!apiResponse.ok) {
      return response.status(404).json({ 
        query: query,
        total_calls: totalCalls,
        response_time: responseTimeSec + "s",
        response_time_ms: responseTimeMs,
        key_expires_on: expiryDate,
        developer: "@dmforbans",
        data: null,
        message: "Data not found"
      });
    }

    let data = await apiResponse.json();
    data = removeCredits(data);

    if (!data || data.ok === false || !data.result) {
      return response.status(404).json({ 
        query: query,
        total_calls: totalCalls,
        response_time: responseTimeSec + "s",
        response_time_ms: responseTimeMs,
        key_expires_on: expiryDate,
        developer: "@dmforbans",
        data: null,
        message: "Data not found"
      });
    }

    return response.status(200).json({
      query: query,
      total_calls: totalCalls,
      response_time: responseTimeSec + "s",
      response_time_ms: responseTimeMs,
      key_expires_on: expiryDate,
      developer: "@dmforbans",
      data: data
    });

  } catch (error) {
    const responseTimeMs = Date.now() - startTime;
    const responseTimeSec = (responseTimeMs / 1000).toFixed(3);

    return response.status(500).json({ 
      query: query,
      total_calls: totalCalls,
      response_time: responseTimeSec + "s",
      response_time_ms: responseTimeMs,
      key_expires_on: expiryDate,
      developer: "@dmforbans",
      data: null,
      message: "Data not found"
    });
  }
}

// 🧹 Credit हटाने का function
function removeCredits(obj) {
  if (!obj || typeof obj !== "object") return obj;
  if (Array.isArray(obj)) return obj.map(item => removeCredits(item));

  const cleaned = {};
  for (const key in obj) {
    const lowerKey = key.toLowerCase();

    if (
      lowerKey === "credit" || lowerKey === "credits" ||
      lowerKey === "developer" || lowerKey === "developed_by" ||
      lowerKey === "developedby" || lowerKey === "author" ||
      lowerKey === "made_by" || lowerKey === "madeby" ||
      lowerKey === "creator" || lowerKey === "created_by" ||
      lowerKey === "createdby" || lowerKey === "powered_by" ||
      lowerKey === "poweredby" || lowerKey === "source" ||
      lowerKey === "src" || lowerKey === "x_traceowner" ||
      lowerKey === "trace_owner"
    ) {
      continue;
    }

    if (typeof obj[key] === "string") {
      const valueLower = obj[key].toLowerCase();
      if (
        valueLower.includes("x_traceowner") ||
        valueLower.includes("@x_traceowner") ||
        valueLower.includes("traceowner") ||
        valueLower.includes("x-trace") ||
        valueLower.includes("x_trace")
      ) {
        continue;
      }
    }

    cleaned[key] = removeCredits(obj[key]);
  }
  return cleaned;
}
