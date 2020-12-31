$(function () {
  const allRationaleInputs = $(".rationale-text-container input[type=radio]");

  // Clear the rationale selection if the user changes answers
  $("input[type=radio][name=second_answer_choice]").on("change", function () {
    const radio = $(this);
    const rationaleId = radio.parents(".rationale").attr("id");
    allRationaleInputs.each(function () {
      const subRadio = $(this);
      if (!(subRadio.parents(".rationale").attr("id") == rationaleId)) {
        subRadio.prop("checked", false);
      }
    });
  });

  // Select the right parent option if the user selects a rationale directly.
  allRationaleInputs.on("click", function () {
    const radio = $(this);
    $("input[type=radio]")
      .not('input[name="' + radio.prop("name") + '"]')
      .prop("checked", false);
    radio
      .parents(".rationale")
      .find("input[type=radio][name=second_answer_choice]")
      .trigger("click");
  });
});
