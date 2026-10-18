(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.GangaQuiz = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  class QuizSession {
    constructor(questions) {
      if (!Array.isArray(questions) || questions.length === 0) {
        throw new Error('The quiz requires at least one question.');
      }

      const ids = new Set();
      questions.forEach((question) => {
        const optionIds = new Set((question.options || []).map((option) => option.id));
        const optionTexts = new Set((question.options || []).map((option) => option.text.trim()));
        if (!question.id || ids.has(question.id)) {
          throw new Error(`Question IDs must be present and unique: ${question.id || '(missing)'}`);
        }
        if (!question.category || !question.question || question.options?.length !== 4 || optionIds.size !== 4 || optionTexts.size !== 4) {
          throw new Error(`Question "${question.id}" must have category and text and exactly four distinct options.`);
        }
        if (!optionIds.has(question.correctOptionId) || !question.explanation || !question.source?.title || !question.source?.reference) {
          throw new Error(`Question "${question.id}" is missing a valid answer, explanation, or source.`);
        }
        ids.add(question.id);
      });

      this.questions = questions;
      this.retry();
    }

    get currentQuestion() {
      return this.questions[this.currentIndex] || null;
    }

    get isComplete() {
      return this.currentIndex >= this.questions.length;
    }

    get selectedOptionId() {
      return this.answers[this.currentIndex]?.selectedOptionId || null;
    }

    get isSubmitted() {
      return Boolean(this.answers[this.currentIndex]?.submitted);
    }

    selectOption(optionId) {
      if (this.isComplete || this.isSubmitted) return false;
      if (!this.currentQuestion.options.some((option) => option.id === optionId)) return false;
      this.answers[this.currentIndex] = { selectedOptionId: optionId, submitted: false };
      return true;
    }

    submitAnswer() {
      if (this.isComplete || this.isSubmitted || !this.selectedOptionId) return null;
      const isCorrect = this.selectedOptionId === this.currentQuestion.correctOptionId;
      this.answers[this.currentIndex].submitted = true;
      if (isCorrect) this.score += 1;
      return { isCorrect, correctOptionId: this.currentQuestion.correctOptionId };
    }

    nextQuestion() {
      if (!this.isSubmitted || this.isComplete) return false;
      this.currentIndex += 1;
      return true;
    }

    retry() {
      this.currentIndex = 0;
      this.score = 0;
      this.answers = {};
    }

    get totalQuestions() {
      return this.questions.length;
    }

    get answeredCount() {
      return this.currentIndex + (this.isSubmitted ? 1 : 0);
    }
  }

  function createQuizController({ document, questions, getMascot = () => null }) {
    const content = document.getElementById('quizContent');
    const announcement = document.getElementById('quizAnnouncement');
    if (!content) throw new Error('Quiz view is missing its content element.');

    const session = new QuizSession(questions);
    let explanationTimer = null;

    function createElement(tag, className, text) {
      const element = document.createElement(tag);
      if (className) element.className = className;
      if (text !== undefined) element.textContent = text;
      return element;
    }

    function playMascotReaction(actionNames) {
      const mascot = getMascot();
      if (!mascot || mascot.currentState !== 'IDLE' || !mascot.is3DReady || !mascot.actions || typeof mascot.playAction !== 'function') {
        return;
      }
      const action = actionNames.find((name) => Object.prototype.hasOwnProperty.call(mascot.actions, name));
      if (!action) return;
      try {
        mascot.playAction(action, 0.4);
      } catch (error) {
        console.warn('[Quiz] Mascot reaction is unavailable:', error);
      }
    }

    function playExplanationReaction() {
      clearTimeout(explanationTimer);
      explanationTimer = setTimeout(() => playMascotReaction(['Pointing_Forward', 'Pointing']), 900);
    }

    function renderProgress() {
      const progress = createElement('progress', 'quiz-progress');
      progress.max = session.totalQuestions;
      progress.value = session.answeredCount;
      progress.setAttribute('aria-label', `${session.answeredCount} of ${session.totalQuestions} questions answered`);
      return progress;
    }

    function renderQuestion() {
      const question = session.currentQuestion;
      const questionNumber = session.currentIndex + 1;
      const wrapper = createElement('div', 'quiz-question-view');
      const meta = createElement('div', 'quiz-question-meta');
      meta.append(
        createElement('span', 'quiz-category', question.category),
        createElement('span', 'quiz-question-count', `Question ${questionNumber} of ${session.totalQuestions}`),
        createElement('span', 'quiz-current-score', `Score ${session.score} / ${session.totalQuestions}`)
      );
      wrapper.append(meta, renderProgress());

      const heading = createElement('h3', 'quiz-question-text', question.question);
      heading.id = 'quizQuestionText';
      wrapper.appendChild(heading);

      const form = createElement('form', 'quiz-form');
      form.id = 'quizAnswerForm';
      const fieldset = createElement('fieldset', 'quiz-options');
      const legend = createElement('legend', 'sr-only', 'Choose one answer');

      question.options.forEach((option) => {
        const label = createElement('label', 'quiz-option');
        const input = document.createElement('input');
        input.type = 'radio';
        input.name = 'quizAnswer';
        input.value = option.id;
        input.checked = session.selectedOptionId === option.id;
        input.disabled = session.isSubmitted;

        const text = createElement('span', 'quiz-option-text', option.text);
        label.append(input, text);
        if (input.checked) label.classList.add('selected');

        if (session.isSubmitted && option.id === question.correctOptionId) {
          label.classList.add('correct');
          label.appendChild(createElement('span', 'quiz-option-result', 'Correct answer'));
        } else if (session.isSubmitted && input.checked) {
          label.classList.add('incorrect');
          label.appendChild(createElement('span', 'quiz-option-result', 'Your answer'));
        }

        fieldset.appendChild(label);
      });

      fieldset.prepend(legend);
      form.appendChild(fieldset);

      if (session.isSubmitted) {
        const result = session.answers[session.currentIndex];
        const correct = result.selectedOptionId === question.correctOptionId;
        const feedback = createElement('section', `quiz-feedback ${correct ? 'feedback-correct' : 'feedback-incorrect'}`);
        feedback.setAttribute('aria-labelledby', 'quizFeedbackTitle');
        const feedbackTitle = createElement('h4', '', correct ? 'Correct!' : 'Not quite');
        feedbackTitle.id = 'quizFeedbackTitle';
        feedback.appendChild(feedbackTitle);
        if (!correct) {
          const correctOption = question.options.find((option) => option.id === question.correctOptionId);
          feedback.appendChild(createElement('p', 'quiz-correct-answer', `Correct answer: ${correctOption.text}`));
        }
        feedback.appendChild(createElement('p', 'quiz-explanation', question.explanation));
        feedback.appendChild(createElement('p', 'quiz-source', `Source: ${question.source.title} — ${question.source.reference}`));
        wrapper.appendChild(feedback);
      }

      const actions = createElement('div', 'quiz-actions');
      if (!session.isSubmitted) {
        const submit = createElement('button', 'submit-btn quiz-submit', 'Submit Answer');
        submit.id = 'quizSubmitButton';
        submit.type = 'submit';
        submit.disabled = !session.selectedOptionId;
        actions.appendChild(submit);
      } else {
        const next = createElement('button', 'submit-btn quiz-next', questionNumber === session.totalQuestions ? 'See Results' : 'Next Question');
        next.id = 'quizNextButton';
        next.type = 'button';
        actions.appendChild(next);
      }

      form.appendChild(actions);
      wrapper.appendChild(form);
      content.replaceChildren(wrapper);

      form.addEventListener('change', (event) => {
        if (event.target.name !== 'quizAnswer' || !session.selectOption(event.target.value)) return;
        fieldset.querySelectorAll('.quiz-option').forEach((option) => option.classList.remove('selected'));
        event.target.closest('.quiz-option').classList.add('selected');
        form.querySelector('#quizSubmitButton').disabled = false;
      });

      form.addEventListener('submit', (event) => {
        event.preventDefault();
        const result = session.submitAnswer();
        if (!result) return;
        const isLastQuestion = session.currentIndex === session.totalQuestions - 1;
        if (announcement) {
          const outcome = result.isCorrect ? 'Correct answer.' : 'Incorrect answer.';
          announcement.textContent = `${outcome} ${question.explanation}${isLastQuestion ? ` Quiz score: ${session.score} out of ${session.totalQuestions}.` : ''}`;
        }
        playMascotReaction(result.isCorrect ? ['Happy_Idle', 'Clapping'] : ['Acknowledging', 'Looking']);
        playExplanationReaction();
        render();
        content.querySelector('#quizNextButton')?.focus();
      });

      form.addEventListener('click', (event) => {
        if (event.target.id !== 'quizNextButton') return;
        clearTimeout(explanationTimer);
        if (!session.nextQuestion()) return;
        if (session.isComplete) {
          playMascotReaction(['Clapping', 'Happy_Idle']);
        }
        render();
        content.querySelector('#quizQuestionText, #quizResultsTitle')?.focus();
      });
    }

    function renderResults() {
      const percentage = Math.round((session.score / session.totalQuestions) * 100);
      const wrapper = createElement('section', 'quiz-results');
      const title = createElement('h3', '', 'Quiz complete!');
      title.id = 'quizResultsTitle';
      title.tabIndex = -1;
      wrapper.append(
        renderProgress(),
        title,
        createElement('p', 'quiz-score', `Your score: ${session.score} out of ${session.totalQuestions}`),
        createElement('p', 'quiz-percentage', `${percentage}%`),
        createElement('p', 'quiz-completion-message', 'Thanks for learning about the Ganga. Keep exploring and sharing what you learned!')
      );

      const actions = createElement('div', 'quiz-actions');
      const retry = createElement('button', 'submit-btn', 'Retry Quiz');
      retry.id = 'quizRetryButton';
      retry.type = 'button';
      const back = createElement('a', 'quiz-secondary-button', 'Back to Chat');
      back.href = '#';
      actions.append(retry, back);
      wrapper.appendChild(actions);
      content.replaceChildren(wrapper);

      retry.addEventListener('click', () => {
        session.retry();
        if (announcement) announcement.textContent = 'Quiz restarted.';
        render();
        content.querySelector('#quizQuestionText')?.focus();
      });
    }

    function render() {
      if (session.isComplete) renderResults();
      else renderQuestion();
    }

    render();
    return session;
  }

  return { QuizSession, createQuizController };
});
