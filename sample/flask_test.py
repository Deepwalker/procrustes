from flask import Flask, render_template
from flask import request
from procrustes.forms import forms

app = Flask(__name__)


class Form(forms.Declarative):
    name = forms.String(min_length=1)
    age = forms.Integer()


@app.route('/', methods=['POST', 'GET'])
def hello():
    if request.form:
        form = Form(request.form, False)
        if form.is_valid():
            print 'Cool!'
        else:
            print form.error
    else:
        form = Form(None)
    return render_template('form.html', form=form)

if __name__ == "__main__":
    app.run()
