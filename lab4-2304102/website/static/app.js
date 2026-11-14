// Browser-side validation (the server checks the same rules again).
document.querySelectorAll("form[data-validate]").forEach(function (form) {
  form.addEventListener("submit", function (e) {
    var errors = [];

    form.querySelectorAll("[data-required]").forEach(function (input) {
      var value = input.type === "password" ? input.value : input.value.trim();
      if (!value) errors.push(input.dataset.required);
    });

    var pw = form.querySelector("[name=password]");
    var cf = form.querySelector("[name=confirm_password]");
    if (pw && cf && pw.value && cf.value && pw.value !== cf.value) {
      errors.push("Passwords do not match");
    }

    form.querySelectorAll("[data-maxlen]").forEach(function (input) {
      if (input.value.trim().length > parseInt(input.dataset.maxlen, 10)) {
        errors.push(input.dataset.toolong);
      }
    });

    // Library: a price must be a number >= 0.
    form.querySelectorAll("[data-number]").forEach(function (input) {
      var v = input.value.trim();
      if (v && (isNaN(Number(v)) || Number(v) < 0)) {
        errors.push(input.dataset.number);
      }
    });

    var box = form.querySelector(".errors");
    if (!box) {
      box = document.createElement("ul");
      box.className = "errors";
      form.insertBefore(box, form.firstChild);
    }
    box.innerHTML = "";
    if (errors.length) {
      e.preventDefault();
      errors.forEach(function (msg) {
        var li = document.createElement("li");
        li.textContent = msg;
        box.appendChild(li);
      });
    }
  });
});

// "Are you sure?" before deleting.
document.querySelectorAll("form[data-confirm]").forEach(function (form) {
  form.addEventListener("submit", function (e) {
    if (!window.confirm(form.dataset.confirm)) e.preventDefault();
  });
});
