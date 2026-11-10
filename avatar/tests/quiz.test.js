'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const questions = require('../quiz-data.js');
const { QuizSession } = require('../quiz.js');

test('question bank has ten source-backed questions with four distinct options each', () => {
  assert.equal(questions.length, 10);
  assert.equal(new Set(questions.map((question) => question.id)).size, questions.length);

  for (const question of questions) {
    assert.ok(question.category);
    assert.ok(question.question);
    assert.equal(question.options.length, 4);
    assert.equal(new Set(question.options.map((option) => option.id)).size, 4);
    assert.equal(new Set(question.options.map((option) => option.text)).size, 4);
    assert.equal(question.options.filter((option) => option.id === question.correctOptionId).length, 1);
    assert.ok(question.explanation);
    assert.ok(question.source.title);
    assert.ok(question.source.reference);
  }

  assert.deepEqual(
    new Set(questions.map((question) => question.category)),
    new Set(['Ganga Knowledge', 'Namami Gange', 'River Pollution', 'Water Quality'])
  );
});

test('session requires one selection, scores a correct answer once, and advances progress', () => {
  const quiz = new QuizSession(questions);
  assert.equal(quiz.answeredCount, 0);
  assert.equal(quiz.submitAnswer(), null);
  assert.equal(quiz.score, 0);
  assert.equal(quiz.nextQuestion(), false);

  const correct = quiz.currentQuestion.correctOptionId;
  assert.equal(quiz.selectOption(correct), true);
  assert.equal(quiz.answeredCount, 0);
  assert.deepEqual(quiz.submitAnswer(), { isCorrect: true, correctOptionId: correct });
  assert.equal(quiz.score, 1);
  assert.equal(quiz.answeredCount, 1);
  assert.equal(quiz.submitAnswer(), null);
  assert.equal(quiz.score, 1);
  assert.equal(quiz.nextQuestion(), true);
  assert.equal(quiz.currentIndex, 1);
  assert.equal(quiz.score, 1);
});

test('incorrect answer earns zero and still locks the answer for explanation feedback', () => {
  const quiz = new QuizSession(questions);
  const wrong = quiz.currentQuestion.options.find((option) => option.id !== quiz.currentQuestion.correctOptionId);
  assert.equal(quiz.selectOption(wrong.id), true);
  assert.deepEqual(quiz.submitAnswer(), {
    isCorrect: false,
    correctOptionId: quiz.currentQuestion.correctOptionId
  });
  assert.equal(quiz.score, 0);
  assert.equal(quiz.isSubmitted, true);
  assert.equal(quiz.selectOption(quiz.currentQuestion.correctOptionId), false);
  assert.equal(quiz.submitAnswer(), null);
  assert.equal(quiz.score, 0);
});

test('completion requires answering every question and retry resets all quiz state', () => {
  const quiz = new QuizSession(questions);

  while (!quiz.isComplete) {
    assert.equal(quiz.currentIndex < quiz.totalQuestions, true);
    assert.equal(quiz.nextQuestion(), false);
    quiz.selectOption(quiz.currentQuestion.correctOptionId);
    assert.ok(quiz.submitAnswer());
    if (quiz.currentIndex < quiz.totalQuestions - 1) assert.equal(quiz.nextQuestion(), true);
    else assert.equal(quiz.nextQuestion(), true);
  }

  assert.equal(quiz.score, 10);
  assert.equal(quiz.answeredCount, 10);
  assert.equal(Math.round((quiz.score / quiz.totalQuestions) * 100), 100);
  assert.equal(quiz.submitAnswer(), null);

  quiz.retry();
  assert.equal(quiz.currentIndex, 0);
  assert.equal(quiz.score, 0);
  assert.equal(quiz.selectedOptionId, null);
  assert.equal(quiz.isSubmitted, false);
  assert.equal(quiz.answeredCount, 0);
  assert.equal(quiz.isComplete, false);
});

test('invalid question data is rejected instead of rendering ambiguous choices', () => {
  const invalid = [{
    ...questions[0],
    options: [
      { id: 'a', text: 'Repeated' },
      { id: 'b', text: 'Repeated' },
      { id: 'c', text: 'Third' },
      { id: 'd', text: 'Fourth' }
    ]
  }];
  assert.throws(() => new QuizSession(invalid), /four distinct options/);
});
