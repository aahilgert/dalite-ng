import { buildReq } from "../ajax.js";

/*********/
/* model */
/*********/
let model;

function initModel(data) {
  model = {
    state: {
      rationales: [],
    },
    urls: {
      getRationales: data.urls.getRationales,
    },
  };
}

/**********/
/* update */
/**********/

async function getRationales(answerUrl) {
  const req = buildReq({}, "get");
  const resp = await fetch(model.urls.getRationales, req);
  model.state.rationales = (await resp.json()).rationales;
  updateTableData(answerUrl);
}

/********/
/* view */
/********/

function initView() {
  initTables();
}

function initTables() {
  document.querySelectorAll("table.display").forEach(elem => {
    // prettier-ignore
    const table = $(elem).DataTable({ // eslint-disable-line
      pageLength: 10,
      dom:
        '<"fg-toolbar ui-toolbar ui-widget-header ui-helper-clearfix ui-corner-tl ui-corner-tr"Bf>t<"fg-toolbar ui-toolbar ui-widget-header ui-helper-clearfix ui-corner-bl ui-corner-br"ip>', // eslint-disable-line
      buttons: [],
    });
    table.order(2, "desc");
  });
}

function updateTableData(answerUrl) {
  const table = $("#flagged-rationales__table").DataTable(); // eslint-disable-line
  table.rows().remove();
  table.rows
    .add(
      model.state.rationales.map(d => [
        d.rationale,
        d.annotator,
        new Date(d.timestamp).toLocaleDateString({
          month: "short",
          day: "numeric",
          year: "numeric",
        }),
        d.note,
        d.answer_pk,
      ]),
    )
    .draw();
  $("#flagged-rationales__table").on('click', 'tr', function () {
      window.location.href = answerUrl+"?q="+this.lastChild.innerHTML;
  });
}

/********/
/* init */
/********/

export async function init(data, answerUrl) {
  initModel(data);
  initView();
  getRationales(answerUrl);
}
