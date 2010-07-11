import cgi
import os

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app


class TestResult(db.Model):
    user = db.UserProperty()
    timestamp = db.DateTimeProperty(auto_now_add=True)
    test_name = db.StringProperty()
    # For example, span of a memory test, the N in an n-back
    test_attr0 = db.IntegerProperty()
    # In a dual-n-back, this could be the the second N if it
    # differs. Seems mean, but legit.
    test_attr1 = db.IntegerProperty()
    # usually, millisecs of reaction.
    result_value = db.IntegerProperty()
    result_correct = db.BooleanProperty()


class Index(webapp.RequestHandler):
    def get(self):
        if not users.get_current_user():
            return self.redirect(users.create_login_url(self.request.uri))
        result_query = TestResult.all().filter("user =", users.get_current_user()).order('-timestamp')
        results = result_query.fetch(100)


        template_values = {
            'results': results,
            }

        path = os.path.join(os.path.dirname(__file__), "templates", 'index.html')
        self.response.out.write(template.render(path, template_values))


class TestHandler(webapp.RequestHandler):
    def get(self):
        if not users.get_current_user():
            return self.redirect(users.create_login_url(self.request.uri))

        path = os.path.join(
            os.path.dirname(__file__), "templates", "tests", self.template_name)
        self.response.out.write(template.render(path, self._get_template_context()))

    def _get_template_context(self):
        return {}

    def post(self):
        if not users.get_current_user():
            return self.redirect(users.create_login_url(self.request.uri))
        results = self.request.POST.getall('results')
        for result in results:
            self._handle_result(result)
        return self.redirect("/")


class VisualReactionTime(TestHandler):
    test_name = "visual-reaction-time"
    template_name = "visual-reaction-time.html"

    def _handle_result(self, result):
        r = TestResult(
            user=users.get_current_user(),
            test_name=self.test_name,
            result_value=int(result),
            result_correct=True,)
        r.put()


class VisualReactionDecisionTime(TestHandler):
    test_name = "visual-reaction-decision-time"
    template_name = "visual-reaction-decision-time.html"

    def _handle_result(self, result):
        ms, correct = result.split(",", 1)
        ms = int(ms)
        correct = correct == "t"
        r = TestResult(
            user=users.get_current_user(),
            test_name=self.test_name,
            result_value=ms,
            result_correct=correct,)
        r.put()


application = webapp.WSGIApplication(
    [('/', Index),
     ('/tests/vrt', VisualReactionTime),
     ('/tests/vrdt', VisualReactionDecisionTime),
     ],
     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
