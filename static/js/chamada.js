// Melhorias da chamada que dependem de JavaScript. Sem ele, a tela continua funcionando.
// - Contador atualizado a cada marcação, em região aria-live (anunciado por leitores de tela).
// - Botão "Marcar todos como presentes" (sugestão da 1ª rodada de validação).
// - Campo "Motivo da falta" só aparece para quem está marcado como ausente.
(function () {
  var contador = document.getElementById("contador-chamada");
  if (!contador) return;
  var form = contador.closest("form");
  var linhas = form.querySelectorAll("fieldset.chamada-linha");
  var botaoTodos = document.getElementById("marcar-todos");

  function atualizarMotivo(linha) {
    var campo = linha.querySelector(".justificativa");
    var ausente = linha.querySelector('input[value="ausente"]:checked');
    if (campo) campo.hidden = !ausente;
  }

  function atualizar() {
    var presentes = form.querySelectorAll('input[value="presente"]:checked').length;
    var ausentes = form.querySelectorAll('input[value="ausente"]:checked').length;
    contador.textContent = linhas.length + " inscritos · " + presentes + " presentes · " + ausentes + " ausentes";
  }

  linhas.forEach(atualizarMotivo);

  form.addEventListener("change", function (evento) {
    if (evento.target.type !== "radio") return;
    atualizarMotivo(evento.target.closest("fieldset"));
    atualizar();
  });

  if (botaoTodos) {
    botaoTodos.hidden = false;
    botaoTodos.addEventListener("click", function () {
      linhas.forEach(function (linha) {
        var marcado = linha.querySelector("input[type=radio]:checked");
        if (!marcado) linha.querySelector('input[value="presente"]').checked = true;
        atualizarMotivo(linha);
      });
      atualizar();
    });
  }
})();
