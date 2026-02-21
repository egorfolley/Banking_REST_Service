const baseUrlInput = document.getElementById("baseUrl");

const state = {
  accessToken: localStorage.getItem("accessToken") || "",
  refreshToken: localStorage.getItem("refreshToken") || "",
};

function apiUrl(path) {
  return `${baseUrlInput.value.replace(/\/$/, "")}${path}`;
}

async function api(path, options = {}) {
  const headers = options.headers || {};
  if (state.accessToken) {
    headers.Authorization = `Bearer ${state.accessToken}`;
  }
  const res = await fetch(apiUrl(path), {
    ...options,
    headers: { "Content-Type": "application/json", ...headers },
  });
  const text = await res.text();
  let data;
  try {
    data = text ? JSON.parse(text) : {};
  } catch (err) {
    data = { raw: text };
  }
  if (!res.ok) {
    throw { status: res.status, data };
  }
  return data;
}

function setTokens(tokens) {
  state.accessToken = tokens.access_token || "";
  state.refreshToken = tokens.refresh_token || "";
  localStorage.setItem("accessToken", state.accessToken);
  localStorage.setItem("refreshToken", state.refreshToken);
}

function show(el, payload) {
  el.textContent = JSON.stringify(payload, null, 2);
}

function bind(id) {
  return document.getElementById(id);
}

bind("pingBtn").addEventListener("click", async () => {
  const output = bind("authOutput");
  try {
    const res = await fetch(apiUrl("/docs"));
    show(output, { ok: res.ok, status: res.status });
  } catch (err) {
    show(output, err);
  }
});

bind("signupBtn").addEventListener("click", async () => {
  const output = bind("authOutput");
  try {
    const data = await api("/api/v1/auth/signup", {
      method: "POST",
      body: JSON.stringify({
        email: bind("signupEmail").value,
        password: bind("signupPassword").value,
      }),
    });
    setTokens(data);
    show(output, data);
  } catch (err) {
    show(output, err);
  }
});

bind("loginBtn").addEventListener("click", async () => {
  const output = bind("authOutput");
  try {
    const data = await api("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({
        email: bind("loginEmail").value,
        password: bind("loginPassword").value,
      }),
    });
    setTokens(data);
    show(output, data);
  } catch (err) {
    show(output, err);
  }
});

bind("refreshBtn").addEventListener("click", async () => {
  const output = bind("authOutput");
  try {
    const data = await api("/api/v1/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: state.refreshToken }),
    });
    setTokens(data);
    show(output, data);
  } catch (err) {
    show(output, err);
  }
});

bind("meBtn").addEventListener("click", async () => {
  const output = bind("authOutput");
  try {
    const data = await api("/api/v1/auth/me");
    show(output, data);
  } catch (err) {
    show(output, err);
  }
});

bind("logoutBtn").addEventListener("click", () => {
  setTokens({});
  show(bind("authOutput"), { ok: true, message: "Logged out" });
});

bind("createHolderBtn").addEventListener("click", async () => {
  const output = bind("holderOutput");
  try {
    const payload = {
      first_name: bind("holderFirst").value,
      last_name: bind("holderLast").value,
      date_of_birth: bind("holderDob").value,
      phone: bind("holderPhone").value,
      address: bind("holderAddress").value,
      ssn_last_four: bind("holderSsn").value,
    };
    const data = await api("/api/v1/account-holders/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    show(output, data);
  } catch (err) {
    show(output, err);
  }
});

bind("getHolderBtn").addEventListener("click", async () => {
  const output = bind("holderOutput");
  try {
    const data = await api("/api/v1/account-holders/me");
    show(output, data);
  } catch (err) {
    show(output, err);
  }
});

bind("updateHolderBtn").addEventListener("click", async () => {
  const output = bind("holderOutput");
  try {
    const payload = {
      first_name: bind("holderFirst").value || undefined,
      last_name: bind("holderLast").value || undefined,
      date_of_birth: bind("holderDob").value || undefined,
      phone: bind("holderPhone").value || undefined,
      address: bind("holderAddress").value || undefined,
      ssn_last_four: bind("holderSsn").value || undefined,
    };
    Object.keys(payload).forEach((key) => payload[key] === undefined && delete payload[key]);
    const data = await api("/api/v1/account-holders/me", {
      method: "PUT",
      body: JSON.stringify(payload),
    });
    show(output, data);
  } catch (err) {
    show(output, err);
  }
});

bind("createAccountBtn").addEventListener("click", async () => {
  const output = bind("accountsOutput");
  try {
    const payload = {
      account_type: bind("accountType").value,
      currency: bind("accountCurrency").value || "USD",
    };
    const depositValue = bind("initialDeposit").value;
    if (depositValue) {
      payload.initial_deposit_cents = Number(depositValue);
    }
    const data = await api("/api/v1/accounts/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    show(output, data);
  } catch (err) {
    show(output, err);
  }
});

bind("listAccountsBtn").addEventListener("click", async () => {
  const output = bind("accountsOutput");
  try {
    const data = await api("/api/v1/accounts/");
    show(output, data);
  } catch (err) {
    show(output, err);
  }
});

bind("getAccountBtn").addEventListener("click", async () => {
  const output = bind("accountsOutput");
  try {
    const id = bind("accountId").value;
    const data = await api(`/api/v1/accounts/${id}`);
    show(output, data);
  } catch (err) {
    show(output, err);
  }
});

bind("updateAccountStatusBtn").addEventListener("click", async () => {
  const output = bind("accountsOutput");
  try {
    const id = bind("accountId").value;
    const data = await api(`/api/v1/accounts/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status: bind("accountStatus").value }),
    });
    show(output, data);
  } catch (err) {
    show(output, err);
  }
});

bind("depositBtn").addEventListener("click", async () => {
  const output = bind("txOutput");
  try {
    const id = bind("txAccountId").value;
    const data = await api(`/api/v1/accounts/${id}/deposit`, {
      method: "POST",
      body: JSON.stringify({
        amount_cents: Number(bind("txAmount").value),
        description: bind("txDesc").value || null,
      }),
    });
    show(output, data);
  } catch (err) {
    show(output, err);
  }
});

bind("withdrawBtn").addEventListener("click", async () => {
  const output = bind("txOutput");
  try {
    const id = bind("txAccountId").value;
    const data = await api(`/api/v1/transactions/${id}/withdraw`, {
      method: "POST",
      body: JSON.stringify({
        amount_cents: Number(bind("txAmount").value),
        description: bind("txDesc").value || null,
      }),
    });
    show(output, data);
  } catch (err) {
    show(output, err);
  }
});

bind("listTxBtn").addEventListener("click", async () => {
  const output = bind("txOutput");
  try {
    const id = bind("txAccountId").value;
    const page = bind("txPage").value || 1;
    const pageSize = bind("txPageSize").value || 20;
    const txType = bind("txType").value;
    const params = new URLSearchParams({ page, page_size: pageSize });
    if (txType) params.set("transaction_type", txType);
    const data = await api(`/api/v1/accounts/${id}/transactions?${params.toString()}`);
    show(output, data);
  } catch (err) {
    show(output, err);
  }
});

bind("transferBtn").addEventListener("click", async () => {
  const output = bind("transferOutput");
  try {
    const data = await api("/api/v1/transfers/", {
      method: "POST",
      body: JSON.stringify({
        idempotency_key: bind("transferKey").value,
        from_account_id: bind("transferFrom").value,
        to_account_id: bind("transferTo").value,
        amount_cents: Number(bind("transferAmount").value),
        description: bind("transferDesc").value || null,
      }),
    });
    show(output, data);
  } catch (err) {
    show(output, err);
  }
});

bind("createCardBtn").addEventListener("click", async () => {
  const output = bind("cardsOutput");
  try {
    const data = await api("/api/v1/cards/", {
      method: "POST",
      body: JSON.stringify({
        account_id: bind("cardAccountId").value,
        card_number: bind("cardNumber").value,
        card_type: bind("cardType").value,
        expiry_month: Number(bind("cardExpiryMonth").value),
        expiry_year: Number(bind("cardExpiryYear").value),
        daily_limit: Number(bind("cardDailyLimit").value),
      }),
    });
    show(output, data);
  } catch (err) {
    show(output, err);
  }
});

bind("listCardsBtn").addEventListener("click", async () => {
  const output = bind("cardsOutput");
  try {
    const data = await api("/api/v1/cards/");
    show(output, data);
  } catch (err) {
    show(output, err);
  }
});

bind("getCardBtn").addEventListener("click", async () => {
  const output = bind("cardsOutput");
  try {
    const id = bind("cardId").value;
    const data = await api(`/api/v1/cards/${id}`);
    show(output, data);
  } catch (err) {
    show(output, err);
  }
});

bind("updateCardStatusBtn").addEventListener("click", async () => {
  const output = bind("cardsOutput");
  try {
    const id = bind("cardId").value;
    const data = await api(`/api/v1/cards/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status: bind("cardStatus").value }),
    });
    show(output, data);
  } catch (err) {
    show(output, err);
  }
});

bind("updateCardLimitBtn").addEventListener("click", async () => {
  const output = bind("cardsOutput");
  try {
    const id = bind("cardId").value;
    const data = await api(`/api/v1/cards/${id}/limit`, {
      method: "PATCH",
      body: JSON.stringify({ daily_limit: Number(bind("cardLimit").value) }),
    });
    show(output, data);
  } catch (err) {
    show(output, err);
  }
});

bind("statementBtn").addEventListener("click", async () => {
  const output = bind("statementOutput");
  try {
    const accountId = bind("statementAccountId").value;
    const params = new URLSearchParams({
      start: bind("statementStart").value,
      end: bind("statementEnd").value,
    });
    const data = await api(`/api/v1/statements/${accountId}?${params.toString()}`);
    show(output, data);
  } catch (err) {
    show(output, err);
  }
});
