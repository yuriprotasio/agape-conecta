// Atualiza o contador da chamada a cada marcação, sem recarregar a página.
// O contador fica em uma região aria-live, então leitores de tela anunciam a mudança.
(function () {
  var contador = document.getElementById("contador-chamada");
  if (!contador) return;
  var form = contador.closest("form");
  var total = form.querySelectorAll("fieldset.chamada-linha").length;

  function atualizar() {
    var presentes = form.querySelectorAll('input[value="presente"]:checked').length;
    var ausentes = form.querySelectorAll('input[value="ausente"]:checked').length;
    contador.textContent = total + " inscritos · " + presentes + " presentes · " + ausentes + " ausentes";
  }

  form.addEventListener("change", function (evento) {
    if (evento.target.type === "radio") atualizar();
  });
})();
