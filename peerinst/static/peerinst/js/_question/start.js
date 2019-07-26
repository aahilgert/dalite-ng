import { buildReq } from "../ajax.js";
import { clear } from "../utils.js";

/**********/
/* update */
/**********/

export function validateFormSubmit(event, url, quality) {
  event.preventDefault();
  const data = {
    quality: quality,
    rationale: document.querySelector("#id_rationale").value,
  };

  const req = buildReq(data, "post");
  fetch(url, req)
    .then(resp => resp.json())
    .then(failed => {
      if (failed.failed.length) {
        toggleQualityError(failed.failed, failed.error_msg);
        document.querySelector("#answer-form").disabled = false;
      } else {
        toggleQualityError();
        document.querySelector("#answer-form").disabled = true;
        document.querySelector("#submit-answer-form").submit();
      }
    })
    .catch(err => console.log(err));
}

/********/
/* view */
/********/

function toggleQualityError(data, errorMsg) {
  if (data) {
    const form = document.querySelector("#submit-answer-form");

    let div = document.querySelector(".errorlist");
    if (!div) {
      div = document.createElement("div");
    }
    clear(div);

    div.classList.add("errorlist");
    div.textContent = errorMsg;

    const ul = document.createElement("ul");
    div.append(ul);
    data.forEach(criterion => {
      const li = document.createElement("li");
      li.textContent = criterion.name;
      li.title = criterion.description;
      ul.append(li);
    });

    form.parentNode.insertBefore(div, form);
  } else {
    const err = document.querySelector("errorlist");
    if (err) {
      err.parentNode.removeChild(err);
    }
  }
}
