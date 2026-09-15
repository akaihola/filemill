export const set = (obj, key, value) => {
  if (obj[key] !== value) obj[key] = value;
};

export const setVar = (el, name, value) => {
  if (el.style.getPropertyValue(name) !== value) {
    el.style.setProperty(name, value);
  }
};
