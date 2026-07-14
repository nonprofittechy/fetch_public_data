for (const select of document.querySelectorAll(".taxonomy-select")) {
  const description = select.parentElement.querySelector(".taxonomy-description");
  const update = () => {
    const item = window.taxonomyLookup[select.value];
    description.textContent = item ? item.description : "Select a label to see its canonical description here.";
  };
  select.addEventListener("change", update);
  update();
}
