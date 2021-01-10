$(function () {
  $(".share-question-answers-summary textarea").on("click", function () {
    $(this).trigger("focus").select();
  });
});
