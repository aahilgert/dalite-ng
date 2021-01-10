import { buildReq } from "../ajax.js";

/*********/
/* model */
/*********/

let model;

function initModel(data) {
  model = {
    canClick: true,
    urls: {
      verify: data.urls.verify,
    },
  };
}

/**********/
/* update */
/**********/

async function verifyUser(elem, username, approve) {
  if (model.canClick) {
    model.canClick = false;
    const req = buildReq(
      {
        username,
        approve,
      },
      "post",
    );
    const resp = await fetch(model.urls.verify, req);
    if (resp.ok) {
      elem.remove();
      setTimeout(() => {
        model.canClick = true;
      }, 500);
      if (!document.querySelectorAll("#new-user-approval li").length) {
        window.location.reload();
      }
    }
  }
}

function initListeners() {
  document.querySelectorAll("#new-user-approval li").forEach((elem) => {
    if (elem.querySelector(".user__username")) {
      const username = elem.querySelector(".user__username").textContent;
      elem
        .querySelector(".user__approve")
        .addEventListener("click", () => verifyUser(elem, username, true));
      elem
        .querySelector(".user__refuse")
        .addEventListener("click", () => verifyUser(elem, username, false));
    }
  });
}

/********/
/* init */
/********/

export function init(data) {
  initModel(data);
  initListeners();
}
