odoo.define('chatbot_automation.tour_launcher', function (require) {
  'use strict';
  const rpc     = require('web.rpc');
  const tour    = require('web_tour.tour');
  const session = require('web.session');

  function mapSteps(steps) {
    return steps.map(step => ({
      content: '',
      trigger: step.selector,
      run() {
        const $el = this.$target;
        $el.addClass('chatbot-highlight');
        setTimeout(() => {
          $el.removeClass('chatbot-highlight');
          if (step.action === 'click')      $el.click();
          else if (step.action === 'type')   $el.val(step.value).trigger('input');
          else if (step.action === 'select') $el.val(step.value).trigger('change');
        }, 600);
      },
    }));
  }

  const POLL_INTERVAL = 1000;
  const poller = setInterval(async () => {
    try {
      const records = await rpc.query({
        model: 'chatbot.tour',
        method: 'search_read',
        args: [
          [
            ['user_id', '=', session.uid],
            ['processed', '=', false],
          ],
          ['id', 'steps'],
        ],
      });
      if (!records.length) {
        return;
      }
      clearInterval(poller);

      const { id, steps } = records[0];
      let parsed;
      try {
        parsed = JSON.parse(steps || '[]');
      } catch {
        parsed = [];
      }
      if (!parsed.length) {
        return;
      }

      await rpc.query({
        model: 'chatbot.tour',
        method: 'write',
        args: [[id], { processed: true }],
      });

      tour.register('dynamic_chatbot_tour', {
        url: window.location.pathname,
        steps: mapSteps(parsed),
      });
      tour.run('dynamic_chatbot_tour');

    } catch (e) {
      console.error('Error running chatbot tour:', e);
    }
  }, POLL_INTERVAL);
});
