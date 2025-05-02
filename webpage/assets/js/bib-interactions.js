document.addEventListener("DOMContentLoaded", function () {
  // Toggle abstract visibility
  document.querySelectorAll(".abstract.btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const hiddenDiv = this.parentNode.parentNode.querySelector(".abstract.hidden");
      if (hiddenDiv) {
        hiddenDiv.style.display = hiddenDiv.style.display === "block" ? "none" : "block";
      }
    });
  });

  // Toggle bibtex visibility
  document.querySelectorAll(".bibtex.btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const hiddenDiv = this.parentNode.parentNode.querySelector(".bibtex.hidden");
      if (hiddenDiv) {
        hiddenDiv.style.display = hiddenDiv.style.display === "block" ? "none" : "block";
      }
    });
  });

  // Toggle award visibility
  document.querySelectorAll(".award.btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const hiddenDiv = this.parentNode.parentNode.querySelector(".award.hidden");
      if (hiddenDiv) {
        hiddenDiv.style.display = hiddenDiv.style.display === "block" ? "none" : "block";
      }
    });
  });
}); 