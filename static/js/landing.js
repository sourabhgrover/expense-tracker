// "See how it works" modal — vanilla JS, no dependencies.
document.addEventListener('DOMContentLoaded', function () {
    var trigger = document.getElementById('how-it-works-btn');
    var modal = document.getElementById('how-it-works-modal');
    var closeBtn = document.getElementById('how-it-works-close');
    var iframe = document.getElementById('how-it-works-iframe');

    // Placeholder YouTube video — swap for the real "how it works" video later.
    var videoSrc = 'https://www.youtube.com/embed/M7lc1UVf-VE';

    if (!trigger || !modal || !closeBtn || !iframe) return;

    function openModal(event) {
        event.preventDefault();
        iframe.src = videoSrc + '?autoplay=1';
        modal.hidden = false;
        document.body.style.overflow = 'hidden';
    }

    function closeModal() {
        modal.hidden = true;
        // Clearing the src (rather than just hiding the modal) actually stops
        // playback instead of leaving the video running behind the overlay.
        iframe.src = '';
        document.body.style.overflow = '';
    }

    trigger.addEventListener('click', openModal);
    closeBtn.addEventListener('click', closeModal);

    modal.addEventListener('click', function (event) {
        if (event.target === modal) {
            closeModal();
        }
    });

    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && !modal.hidden) {
            closeModal();
        }
    });
});
