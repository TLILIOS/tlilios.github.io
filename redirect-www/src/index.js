// 301 permanent vers l'apex en préservant chemin et query string.
export default {
  fetch(request) {
    const url = new URL(request.url);
    url.hostname = "primapp.dev";
    url.protocol = "https:";
    return Response.redirect(url.toString(), 301);
  },
};
