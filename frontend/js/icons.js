function mi(name) {
  return '<span class="mi">' + name + "</span>";
}
function miFor(emoji) {
  return MI[emoji] ? mi(MI[emoji]) : emoji;
}
