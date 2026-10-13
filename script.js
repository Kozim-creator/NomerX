
const STORAGE_KEY = "nomer_x_accounts_v5";
const SESSION_KEY = "nomer_x_session_v5";
const PROMO_KEY = "nomer_x_promos_v5";
const SPIN_PRICE = 1000;

const ADMIN_LOGIN = "kozim_admin";
const ADMIN_PASSWORD = "Kozim_Change_927!";

const STARTER_CARS = [
  { id: "starter_bmw", name: "BMW M4", price: 0, emoji: "🏎️", installedPlate: null },
  { id: "starter_g63", name: "Mercedes G63", price: 0, emoji: "🚙", installedPlate: null }
];

const cars = [
  { id: "bmw", name: "BMW M4", price: 20000, emoji: "🏎️" },
  { id: "mercedes", name: "Mercedes-AMG", price: 30000, emoji: "🚘" },
  { id: "lambo", name: "Lamborghini", price: 50000, emoji: "🏎️" },
  { id: "bugatti", name: "Bugatti Chiron", price: 100000, emoji: "🚀" },
  { id: "g63", name: "Mercedes G63", price: 40000, emoji: "🚙" },
  { id: "supra", name: "Toyota Supra", price: 25000, emoji: "🏁" },
  { id: "porsche", name: "Porsche 911", price: 60000, emoji: "🏎️" },
  { id: "audi", name: "Audi RS7", price: 45000, emoji: "🚘" },
  { id: "mclaren", name: "McLaren 720S", price: 90000, emoji: "🏎️" },
  { id: "rolls", name: "Rolls-Royce", price: 120000, emoji: "🚘" }
];

const numberOffers = [
  { plate: "A777AA", rarity: "Редкий", price: 1500000 },
  { plate: "M555MM", rarity: "Редкий", price: 800000 },
  { plate: "B123BC", rarity: "Обычный", price: 85000 },
  { plate: "X000XX", rarity: "Редкий", price: 2500000 },
  { plate: "V111VV", rarity: "Редкий", price: 1200000 },
  { plate: "C404CC", rarity: "Обычный", price: 65000 },
  { plate: "D777DD", rarity: "Редкий", price: 1800000 },
  { plate: "T123TT", rarity: "Обычный", price: 90000 }
];

// ---------- STORAGE ----------

function readJSON(key, fallback) {
  try {
    return JSON.parse(localStorage.getItem(key)) ?? fallback;
  } catch {
    return fallback;
  }
}

function getAccounts() {
  let accounts = readJSON(STORAGE_KEY, null);

  if (!accounts) {
    for (const oldKey of [
      "nomer_x_accounts_v4",
      "nomer_x_accounts_v3",
      "nomer_x_accounts"
    ]) {
      const oldData = readJSON(oldKey, null);

      if (oldData && typeof oldData === "object") {
        accounts = oldData;
        localStorage.setItem(STORAGE_KEY, JSON.stringify(accounts));
        break;
      }
    }
  }

  return accounts || {};
}

function saveAccounts(accounts) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(accounts));
}

function getPromos() {
  return readJSON(PROMO_KEY, {});
}

function savePromos(promos) {
  localStorage.setItem(PROMO_KEY, JSON.stringify(promos));
}

function currentSession() {
  return readJSON(SESSION_KEY, null);
}

function currentUser() {
  const session = currentSession();
  if (!session || session.admin) return null;
  return getAccounts()[session.username] || null;
}

function saveCurrentUser(user) {
  const accounts = getAccounts();
  accounts[user.username] = user;
  saveAccounts(accounts);
}

function setMessage(id, message) {
  const el = document.getElementById(id);
  if (el) el.textContent = message;
}

function escapeHTML(value) {
  return String(value).replace(/[&<>"']/g, ch => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;"
  })[ch]);
}

// ---------- ВОССТАНОВЛЕНИЕ СТАРТОВОГО НАБОРА ----------

function repairPlayer(user) {
  let changed = false;

  if (!Array.isArray(user.numbers)) {
    user.numbers = [];
    changed = true;
  }

  if (!Array.isArray(user.cars)) {
    user.cars = [];
    changed = true;
  }

  if (!Array.isArray(user.history)) {
    user.history = [];
    changed = true;
  }

  if (!Array.isArray(user.usedPromos)) {
    user.usedPromos = [];
    changed = true;
  }

  if (!Number.isFinite(Number(user.coins))) {
    user.coins = 0;
    changed = true;
  }

  if (!user.starterPackApplied) {
    user.coins += 50000;

    for (const starter of STARTER_CARS) {
      const exists = user.cars.some(car =>
        car.id === starter.id ||
        (car.name === starter.name && Number(car.price) === 0)
      );

      if (!exists) user.cars.push({ ...starter });
    }

    user.starterPackApplied = true;
    changed = true;
  }

  if (changed) saveCurrentUser(user);
  return user;
}

// ---------- REGISTRATION ----------

function register() {
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;

  if (!/^[a-zA-Z0-9_]{3,20}$/.test(username)) {
    setMessage("authMessage", "Логин: 3–20 латинских букв, цифр или _.");
    return;
  }

  if (password.length < 4) {
    setMessage("authMessage", "Пароль должен быть минимум 4 символа.");
    return;
  }

  if (username.toLowerCase() === ADMIN_LOGIN.toLowerCase()) {
    setMessage("authMessage", "Этот логин зарезервирован.");
    return;
  }

  const accounts = getAccounts();

  if (accounts[username]) {
    setMessage("authMessage", "Этот логин уже занят.");
    return;
  }

  accounts[username] = {
    username,
    password,
    coins: 50000,
    numbers: [],
    cars: STARTER_CARS.map(car => ({ ...car })),
    history: [],
    usedPromos: [],
    starterPackApplied: true
  };

  saveAccounts(accounts);
  localStorage.setItem(SESSION_KEY, JSON.stringify({ username }));
  enterGame();
}

function login() {
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;

  if (username === ADMIN_LOGIN && password === ADMIN_PASSWORD) {
    localStorage.setItem(
      SESSION_KEY,
      JSON.stringify({ username: ADMIN_LOGIN, admin: true })
    );
    showAdminLogin();
    return;
  }

  const user = getAccounts()[username];

  if (!user || user.password !== password) {
    setMessage("authMessage", "Неверный логин или пароль.");
    return;
  }

  repairPlayer(user);
  localStorage.setItem(SESSION_KEY, JSON.stringify({ username }));
  enterGame();
}

function logout() {
  localStorage.removeItem(SESSION_KEY);
  document.getElementById("authPanel").hidden = false;
  document.getElementById("gamePanel").hidden = true;
  document.getElementById("adminNav").hidden = true;
  setMessage("authMessage", "");
}

function isAdmin() {
  const session = currentSession();

  return Boolean(
    session &&
    session.admin === true &&
    session.username === ADMIN_LOGIN
  );
}

function showAdminLogin() {
  document.getElementById("authPanel").hidden = true;
  document.getElementById("gamePanel").hidden = false;
  document.getElementById("adminNav").hidden = false;
  document.getElementById("playerName").textContent = "ADMIN";

  showTab("adminTab");
  updateBalance();
  renderAdmin();
}

function enterGame() {
  let user = currentUser();

  if (!user) {
    logout();
    return;
  }

  user = repairPlayer(user);

  document.getElementById("authPanel").hidden = true;
  document.getElementById("gamePanel").hidden = false;
  document.getElementById("playerName").textContent = user.username;
  document.getElementById("adminNav").hidden = true;

  showTab("spinTab");
  updateBalance();
  renderAll();
}

// ---------- NAVIGATION ----------

function showTab(tabId) {
  if (tabId === "adminTab" && !isAdmin()) return;

  document.querySelectorAll(".tab").forEach(tab => {
    tab.hidden = tab.id !== tabId;
  });

  if (tabId === "shopTab") renderShop();
  if (tabId === "garageTab") renderGarage();
  if (tabId === "historyTab") renderHistory();
  if (tabId === "adminTab") renderAdmin();
}

function updateBalance() {
  const el = document.getElementById("balance");
  const user = currentUser();

  if (el) {
    el.textContent = user
      ? Number(user.coins).toLocaleString("ru-RU")
      : "—";
  }
}

// ---------- NUMBER GENERATION ----------

// Формат: V000VV, A527BC, M777MM.
function randomPlate() {
  const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  const letter = () => letters[Math.floor(Math.random() * letters.length)];
  const digit = () => Math.floor(Math.random() * 10);

  return `${letter()}${digit()}${digit()}${digit()}${letter()}${letter()}`;
}

function getBeautyScore(plate) {
  const digits = plate.slice(1, 4);
  const letters = plate[0] + plate.slice(4, 6);
  let score = 0;

  if (digits[0] === digits[1] && digits[1] === digits[2]) score += 5;
  if (digits[0] === digits[2]) score += 2;
  if (new Set(digits).size === 1) score += 3;

  if (letters[0] === letters[1] && letters[1] === letters[2]) score += 5;
  if (new Set(letters).size === 1) score += 2;

  if (["000", "111", "222", "333", "555", "777", "888", "999"].includes(digits)) {
    score += 2;
  }

  return Math.min(score, 10);
}

function getNumberPrice(plate, rarity) {
  const score = getBeautyScore(plate);
  const random = Math.random();

  const min = rarity === "Редкий" ? 20000 : 10000;
  const max = rarity === "Редкий" ? 30000000 : 500000;

  // Красивые номера получают заметную прибавку к цене.
  const price = min
    + random * (max - min) * 0.5
    + (score / 10) * (max - min) * 0.5;

  return Math.floor(Math.min(max, Math.max(min, price)));
}

// ---------- SPIN ----------

function spinNumber() {
  const user = currentUser();
  if (!user) return;

  if (user.coins < SPIN_PRICE) {
    setMessage("spinResult", "Недостаточно монет! Нужно 1 000.");
    return;
  }

  user.coins -= SPIN_PRICE;
  saveCurrentUser(user);
  updateBalance();

  const button = document.getElementById("spinButton");
  const display = document.getElementById("spinDisplay");

  button.disabled = true;
  setMessage("spinResult", "🎰 Крутим номер...");

  let ticks = 0;

  const animation = setInterval(() => {
    display.textContent = randomPlate();
    ticks++;

    if (ticks >= 12) {
      clearInterval(animation);

      const rarity = Math.random() < 0.10 ? "Редкий" : "Обычный";
      const plate = randomPlate();
      const price = getNumberPrice(plate, rarity);
      const date = new Date().toLocaleString("ru-RU");

      user.numbers.push({
        plate, rarity, price, sold: false, date
      });

      user.history.unshift({
        plate, rarity, price, action: "Получен", date
      });

      saveCurrentUser(user);

      display.textContent = plate;
      display.style.borderColor =
        rarity === "Редкий" ? "#f6c453" : "#dbe4ee";

      setMessage(
        "spinResult",
        `${rarity}! ${plate} · Цена: ${price.toLocaleString("ru-RU")} монет`
      );

      button.disabled = false;
      updateBalance();
      renderAll();
    }
  }, 100);
}

// ---------- SHOP ----------

function renderShop() {
  const user = currentUser();
  if (!user) return;

  document.getElementById("carShop").innerHTML = cars.map(car => {
    const owned = user.cars.some(item => item.id === car.id);

    return `
      <article class="item">
        <h3>${car.emoji} ${escapeHTML(car.name)}</h3>
        <p>Цена: ${car.price.toLocaleString("ru-RU")} монет</p>
        <button ${owned ? "disabled" : ""} onclick="buyCar('${car.id}')">
          ${owned ? "Уже куплено" : "Купить"}
        </button>
      </article>
    `;
  }).join("");

  document.getElementById("numberShop").innerHTML = numberOffers.map((number, index) => `
    <article class="item">
      <div class="plate">${escapeHTML(number.plate)}</div>
      <p class="rarity ${number.rarity === "Редкий" ? "rare" : ""}">
        ${escapeHTML(number.rarity)}
      </p>
      <p>Цена: ${number.price.toLocaleString("ru-RU")} монет</p>
      <button onclick="buyShopNumber(${index})">Купить номер</button>
    </article>
  `).join("");
}

function buyCar(carId) {
  const user = currentUser();
  const car = cars.find(item => item.id === carId);

  if (!user || !car) return;

  if (user.cars.some(item => item.id === car.id || item.name === car.name)) {
    alert("Такая машина уже есть в гараже.");
    return;
  }

  if (user.coins < car.price) {
    alert("Недостаточно монет.");
    return;
  }

  user.coins -= car.price;
  user.cars.push({ ...car, installedPlate: null });

  saveCurrentUser(user);
  updateBalance();
  renderAll();
}

function buyShopNumber(index) {
  const user = currentUser();
  const offer = numberOffers[index];

  if (!user || !offer) return;

  if (user.coins < offer.price) {
    alert("Недостаточно монет.");
    return;
  }

  user.coins -= offer.price;

  user.numbers.push({
    ...offer,
    sold: false,
    date: new Date().toLocaleString("ru-RU")
  });

  user.history.unshift({
    ...offer,
    action: "Куплен",
    date: new Date().toLocaleString("ru-RU")
  });

  saveCurrentUser(user);
  updateBalance();
  renderAll();
}

// ---------- GARAGE ----------

function renderGarage() {
  const user = currentUser();
  if (!user) return;

  document.getElementById("garageCars").innerHTML = user.cars.length
    ? user.cars.map((car, index) => `
      <article class="item">
        <h3>${car.emoji || "🚘"} ${escapeHTML(car.name)}</h3>
        <p>Номер: ${escapeHTML(car.installedPlate || "Не установлен")}</p>
        <button onclick="installPlate(${index})">Установить номер</button>
      </article>
    `).join("")
    : "<p>Машин пока нет.</p>";

  const available = user.numbers
    .map((number, index) => ({ ...number, index }))
    .filter(number => !number.sold);

  document.getElementById("myNumbers").innerHTML = available.length
    ? available.map(number => `
      <article class="item">
        <div class="plate">${escapeHTML(number.plate)}</div>
        <p class="rarity ${number.rarity === "Редкий" ? "rare" : ""}">
          ${escapeHTML(number.rarity)}
        </p>
        <p>Цена: ${Number(number.price).toLocaleString("ru-RU")} монет</p>
        <button onclick="sellNumber(${number.index})">Продать номер</button>
      </article>
    `).join("")
    : "<p>Номеров пока нет.</p>";
}

function installPlate(carIndex) {
  const user = currentUser();
  if (!user || !user.cars[carIndex]) return;

  const available = user.numbers.filter(number => !number.sold);

  if (!available.length) {
    alert("Сначала получи или купи номер.");
    return;
  }

  const choice = prompt(
    "Введи номер из своей коллекции:\n" +
    available.map(number => number.plate).join(", ")
  );

  if (!choice) return;

  const number = available.find(
    item => item.plate.toUpperCase() === choice.trim().toUpperCase()
  );

  if (!number) {
    alert("Такого номера нет в твоей коллекции.");
    return;
  }

  user.cars[carIndex].installedPlate = number.plate;
  saveCurrentUser(user);
  renderGarage();
}

// ---------- SELL ----------

function sellNumber(index) {
  const user = currentUser();
  if (!user) return;

  const number = user.numbers[index];
  if (!number || number.sold) return;

  const price = Number(number.price);

  if (!Number.isFinite(price) || price < 0) {
    alert("Ошибка цены номера.");
    return;
  }

  if (!confirm(
    `Продать ${number.plate} за ${price.toLocaleString("ru-RU")} монет?`
  )) return;

  number.sold = true;
  user.coins += price;

  user.history.unshift({
    plate: number.plate,
    rarity: number.rarity,
    price,
    action: "Продан",
    date: new Date().toLocaleString("ru-RU")
  });

  saveCurrentUser(user);
  updateBalance();
  renderAll();
}

// ---------- HISTORY ----------

function renderHistory() {
  const user = currentUser();
  if (!user) return;

  document.getElementById("historyList").innerHTML = user.history.length
    ? user.history.map(item => `
      <div class="historyEntry">
        <b>${escapeHTML(item.plate)}</b> · ${escapeHTML(item.rarity)}
        <br>Цена: ${Number(item.price).toLocaleString("ru-RU")} монет
        <br>${escapeHTML(item.action || "Получен")}
        <br><small>${escapeHTML(item.date || "")}</small>
      </div>
    `).join("")
    : "<p>История пока пустая.</p>";
}

// ---------- PROMOS ----------

function usePromo() {
  const user = currentUser();
  if (!user) return;

  const code = document.getElementById("promoInput").value.trim().toUpperCase();
  const promo = getPromos()[code];

  if (!promo) {
    setMessage("promoMessage", "Промокод не найден.");
    return;
  }

  if (user.usedPromos.includes(code)) {
    setMessage("promoMessage", "Ты уже использовал этот промокод.");
    return;
  }

  user.coins += Number(promo.amount);
  user.usedPromos.push(code);

  saveCurrentUser(user);
  updateBalance();

  setMessage(
    "promoMessage",
    `Получено ${Number(promo.amount).toLocaleString("ru-RU")} монет!`
  );
}

// ---------- ADMIN ----------

function createPromo() {
  if (!isAdmin()) return;

  const code = document.getElementById("newPromo").value.trim().toUpperCase();
  const amount = Number(document.getElementById("newPromoAmount").value);

  if (!/^[A-Z0-9_-]{3,24}$/.test(code) ||
      !Number.isSafeInteger(amount) || amount < 1) {
    setMessage("adminMessage", "Проверь код и сумму награды.");
    return;
  }

  const promos = getPromos();

  if (promos[code]) {
    setMessage("adminMessage", "Этот промокод уже существует.");
    return;
  }

  promos[code] = { amount };
  savePromos(promos);

  setMessage("adminMessage", `Создан промокод ${code}.`);
  renderAdmin();
}

function giveCoins() {
  if (!isAdmin()) return;

  const username = document.getElementById("adminPlayer").value.trim();
  const amount = Number(document.getElementById("adminCoins").value);
  const accounts = getAccounts();
  const user = accounts[username];

  if (!user) {
    setMessage("adminMessage", "Игрок не найден.");
    return;
  }

  if (!Number.isSafeInteger(amount) || amount < 1) {
    setMessage("adminMessage", "Введи положительное количество монет.");
    return;
  }

  user.coins += amount;
  accounts[username] = user;
  saveAccounts(accounts);

  setMessage(
    "adminMessage",
    `Игроку ${username} выдано ${amount.toLocaleString("ru-RU")} монет.`
  );

  renderAdmin();
}

function renderAdmin() {
  if (!isAdmin()) return;

  const players = Object.values(getAccounts());

  document.getElementById("playersList").innerHTML = players.length
    ? players.map(user => `
      <div class="listEntry">
        <b>${escapeHTML(user.username)}</b>
        · ${Number(user.coins).toLocaleString("ru-RU")} монет
      </div>
    `).join("")
    : "<p>Игроков пока нет.</p>";

  const promos = Object.entries(getPromos());

  document.getElementById("promoList").innerHTML = promos.length
    ? promos.map(([code, promo]) => `
      <div class="listEntry">
        <b>${escapeHTML(code)}</b>
        — ${Number(promo.amount).toLocaleString("ru-RU")} монет
        <button onclick="deletePromo('${encodeURIComponent(code)}')">
          Удалить
        </button>
      </div>
    `).join("")
    : "<p>Промокодов пока нет.</p>";
}

function deletePromo(encodedCode) {
  if (!isAdmin()) return;

  const promos = getPromos();
  delete promos[decodeURIComponent(encodedCode)];
  savePromos(promos);
  renderAdmin();
}

// ---------- REFRESH ----------

function renderAll() {
  renderShop();
  renderGarage();
  renderHistory();
}

function initialize() {
  const accounts = getAccounts();
  let changed = false;

  // Исправляем старые профили без повторной выдачи стартового набора.
  // Набор выдаётся только если у профиля ещё нет отметки.
  for (const username of Object.keys(accounts)) {
    const user = accounts[username];
    if (!user || username === ADMIN_LOGIN) continue;

    if (!user.starterPackApplied) {
      if (!Array.isArray(user.cars)) user.cars = [];
      if (!Array.isArray(user.numbers)) user.numbers = [];
      if (!Array.isArray(user.history)) user.history = [];
      if (!Array.isArray(user.usedPromos)) user.usedPromos = [];
      if (!Number.isFinite(Number(user.coins))) user.coins = 0;

      user.coins += STARTING_COINS;

      for (const starter of STARTER_CARS) {
        const exists = user.cars.some(car =>
          car.id === starter.id ||
          (car.name === starter.name && Number(car.price) === 0)
        );
        if (!exists) user.cars.push({ ...starter });
      }

      user.starterPackApplied = true;
      changed = true;
    }
  }

  if (changed) saveAccounts(accounts);

  const session = currentSession();

  if (session && session.admin && session.username === ADMIN_LOGIN) {
    showAdminLogin();
  } else if (currentUser()) {
    enterGame();
  } else {
    document.getElementById("authPanel").hidden = false;
    document.getElementById("gamePanel").hidden = true;
  }
}

initialize();
