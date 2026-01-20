$(document).ready(function () {
  // Force reload when navigating back to prevent showing cached deleted comments
  window.addEventListener("pageshow", function (event) {
    if (
      event.persisted ||
      (window.performance && window.performance.navigation.type === 2)
    ) {
      // Page was loaded from cache (back button), reload to get fresh data
      window.location.reload();
    }
  });

  $("#post-form").submit(function (e) {
    e.preventDefault(); //prevent form from refreshing after click submit btn

    let post_caption = $("#post-caption").val()
      ? $("#post-caption").val().trim()
      : "";
    let post_visibility = $("#visibility").val();

    // Client-side validation: caption is required
    if (!post_caption) {
      if (window.UIkit && typeof UIkit.notification === "function") {
        UIkit.notification({
          message: "Please add a caption before posting.",
          status: "warning",
          pos: "top-right",
          timeout: 3000,
        });
      } else {
        alert("Please add a caption before posting.");
      }
      return false;
    }

    let formData = new FormData(); //send date to a server
    formData.append("post-caption", post_caption); //the latter = actual value
    formData.append("visibility", post_visibility);

    // If an item listing is selected (either select or dropdown button), include it but do not block posting if empty
    let itemId = "";
    const $itemSelect = $("#item-listings-select");
    if ($itemSelect.length && !$itemSelect.prop("disabled")) {
      itemId = $itemSelect.val() || "";
    } else {
      const $listingBtn = $("#select-item-listings");
      if ($listingBtn.length) {
        itemId = $listingBtn.data("selected-id") || "";
      }
    }
    formData.append("rental_item", itemId);

    // Require a rental item when posting "Open for Rent"
    if (post_visibility === "Open for Rent") {
      const hasItems =
        ($itemSelect.length &&
          $itemSelect.find("option").filter(function () {
            return (
              $(this).val() &&
              $(this).val().toString().trim() !== "" &&
              !$(this).is(":disabled")
            );
          }).length > 0) ||
        $("#item-listings-dropdown li[data-value]").length > 0;

      if (!hasItems) {
        if (window.UIkit && typeof UIkit.notification === "function") {
          UIkit.notification({
            message:
              "Add a rental item in your profile before posting as Open for Rent.",
            status: "warning",
            pos: "top-right",
            timeout: 4000,
          });
        } else {
          alert("Add a rental item before posting as Open for Rent.");
        }
        return false;
      }

      if (!itemId) {
        if (window.UIkit && typeof UIkit.notification === "function") {
          UIkit.notification({
            message: "Please select which item you are renting out.",
            status: "warning",
            pos: "top-right",
            timeout: 4000,
          });
        } else {
          alert("Please select which item you are renting out.");
        }
        return false;
      }
    }

    let fileInput = $("#post-thumbnail")[0];
    let files = fileInput.files;

    if (files && files.length > 0) {
      for (let i = 0; i < files.length; i++) {
        formData.append("post-thumbnail", files[i], files[i].name);
      }
    } else {
      formData.append("post-thumbnail", null);
    }

    $.ajax({
      url: "/create_post/",
      type: "POST",
      dataType: "json",
      data: formData,
      processData: false, //prevent jQuery from validate the img
      contentType: false,

      //keep track when things masuk dlm app
      success: function (res) {
        let imageHtml = "";
        if (res.post.images && res.post.images.length > 0) {
          imageHtml = '<div class="grid grid-cols-2 gap-2 px-5">';
          res.post.images.forEach((imgUrl) => {
            imageHtml += `
              <a href="${imgUrl}" class="col-span-2">
                <img src="${imgUrl}"
                    style="width: 100%; height: 300px; object-fit: cover;"
                    class="rounded-md w-full lg:h-76 object-cover" />
              </a>
            `;
          });
          imageHtml += "</div>";
        }

        // Build product details HTML if present
        let productHtml = "";
        if (res.post.product) {
          const itemUrl = `/item/${res.post.product.slug}/`;
          productHtml = `
            <div class="p-5 pt-3 border-b dark:border-gray-700">
              <a href="${itemUrl}" class="flex space-x-3 items-start bg-gray-50 dark:bg-gray-800 p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition">
                <img src="${
                  res.post.product.image
                }" class="w-20 h-20 rounded-md object-cover" alt="${
            res.post.product.title
          }" />
                <div class="flex-1 space-y-1">
                  <div class="font-semibold text-gray-800 dark:text-gray-100">${
                    res.post.product.title
                  }</div>
                  ${
                    res.post.product.description
                      ? `<div class="text-sm text-gray-600 dark:text-gray-400">${res.post.product.description}</div>`
                      : ""
                  }
                  ${
                    res.post.product.location
                      ? `<div class="text-sm text-gray-600 dark:text-gray-400"><i class="uil-map-marker"></i> ${res.post.product.location}</div>`
                      : ""
                  }
                  <div class="text-sm font-medium text-blue-600 dark:text-blue-400">Daily rate: RM ${
                    res.post.product.daily_rate
                  }</div>
                </div>
              </a>
            </div>
          `;
        }

        let _html =
          '<div id="post-card-' +
          res.post.id +
          '" class="card lg:mx-0 uk-animation-slide-bottom-small mt-3 mb-3">\
            <div class="flex justify-between items-center lg:p-4 p-2.5">\
                <div class="flex flex-1 items-center space-x-4">\
                    <a href="#">\
                        <img src="' +
          res.post.profile_image +
          '" style="width: 40px; height: 40px;" class="bg-gray-200 border border-white rounded-full w-10 h-10" />\
                    </a>\
                    <div class="flex-1 font-semibold capitalize">\
                        <a href="#" class="text-black dark:text-gray-100">' +
          res.post.full_name +
          '</a>\
                        <div class="text-gray-700 flex items-center space-x-2">' +
          res.post.date +
          ' ago \
                        </div>\
                    </div>\
                </div>\
                <div>\
                    <a href="#"> <i class="icon-feather-more-horizontal text-2xl hover:bg-gray-200 rounded-full p-2 transition -mr-1 dark:hover:bg-gray-700"></i> </a>\
                    <div class="bg-white w-56 shadow-md mx-auto p-2 mt-12 rounded-md text-gray-500 hidden text-base border border-gray-100 dark:bg-gray-900 dark:text-gray-100 dark:border-gray-700" uk-drop="mode: click;pos: bottom-right;animation: uk-animation-slide-bottom-small">\
                        <ul class="space-y-1">\
                            <li>\
                                <a href="#" class="flex items-center px-3 py-2 hover:bg-gray-200 hover:text-gray-800 rounded-md dark:hover:bg-gray-800">\
                            <i class="uil-bookmark mr-1"></i>  Save Post \
                            </a>\
                            </li>\
                            <li>\
                                <hr class="-mx-2 my-2 dark:border-gray-800">\
                            </li>\
                            <li>\
                                <a href="#" class="flex items-center px-3 py-2 text-red-500 hover:bg-red-100 hover:text-red-500 rounded-md dark:hover:bg-red-600 delete-post-btn" data-post-id="' +
          res.post.id +
          '">\
                            <i class="uil-trash-alt mr-1"></i>  Delete\
                            </a>\
                            </li>\
                        </ul>\
                    </div>\
                </div>\
            </div>\
            <div uk-lightbox>\
                    <div class="p-5 pt-0 border-b dark:border-gray-700 pb-3">\
                        ' +
          res.post.title +
          "\
                    </div>\
               " +
          imageHtml +
          "\
            </div>\
            " +
          productHtml +
          '\
            <div class="p-4 space-y-3">\
                <div class="flex space-x-4 lg:font-bold">\
                    <a  class="flex items-center space-x-2  text-blue-500" style="cursor: pointer;" >\
                        <div class="p-2 rounded-full like-btn' +
          res.post.id +
          ' text-black " id="like-btn" data-like-btn="' +
          res.post.id +
          '">\
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" width="22" height="22" class="dark:text-blue-100">\
                                <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z" />\
                            </svg>\
                        </div>\
                        <div> Like</div>\
                    </a>\
                    <a href="#" class="flex items-center space-x-2">\
                        <div class="p-2 rounded-full  text-black lg:bg-gray-100 dark:bg-gray-600">\
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" width="22" height="22" class="dark:text-gray-100">\
                                <path fill-rule="evenodd" d="M18 5v8a2 2 0 01-2 2h-5l-5 4v-4H4a2 2 0 01-2-2V5a2 2 0 012-2h12a2 2 0 012 2zM7 8H5v2h2V8zm2 0h2v2H9V8zm6 0h-2v2h2V8z" clip-rule="evenodd" />\
                            </svg>\
                        </div>\
                        <div> <b><span id="comment-count' +
          res.post.id +
          '">0</span></b> Comment</div>\
                    </a>\
                    <a href="#" class="flex items-center space-x-2 flex-1 justify-end">\
                        <div class="p-2 rounded-full  text-black lg:bg-gray-100 dark:bg-gray-600">\
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" width="22" height="22" class="dark:text-gray-100">\
                                <path d="M15 8a3 3 0 10-2.977-2.63l-4.94 2.47a3 3 0 100 4.319l4.94 2.47a3 3 0 10.895-1.789l-4.94-2.47a3.027 3.027 0 000-.74l4.94-2.47C13.456 7.68 14.19 8 15 8z" />\
                            </svg>\
                        </div>\
                        <div> Share</div>\
                    </a>\
                </div>\
                <div class="flex items-center space-x-3 pt-2">\
                    \
                    <div class="dark:text-gray-100">\
                        <strong><span id="like-count' +
          res.post.id +
          '">0</span></strong> Likes\
                    </div>\
                </div>\
                <div class="border-t py-4 space-y-4 dark:border-gray-600" id="comment-div' +
          res.post.id +
          '">\
                </div>\
                  <div class="flex">\
                <div class="text-gray-700 py-2 px-3 rounded-md bg-gray-100 relative lg:ml-5 ml-2 lg:mr-12 dark:bg-gray-800 dark:text-gray-100">\
                  <a href="#" class="hover:text-blue-600 hover:underline">No Comments Yet </a> \
                </div>\
                </div>\
                    <div class="bg-gray-100 rounded-full relative dark:bg-gray-800 border-t">\
                        <input placeholder="Add your Comment..." id="comment-input' +
          res.post.id +
          '" data-comment-input="' +
          res.post.id +
          '" class="bg-transparent max-h-10 shadow-none px-5 comment-input' +
          res.post.id +
          '">\
                        <div class="-m-0.5 absolute bottom-0 flex items-center right-3 text-xl">\
                            <a style="cursor: pointer;" id="comment-btn" class="comment-btn' +
          res.post.id +
          '" data-comment-btn="' +
          res.post.id +
          '">\
                                <ion-icon name="send-outline" class="hover:bg-gray-200 p-1.5 rounded-full"></ion-icon>\
                            </a>\
                        </div>\
                    </div>\
                </div>\
        </div>\
            ';

        $("#create-post-modal").removeClass("uk-flex uk-open");
        // Debug: log the saved visibility returned by server
        try {
          console.log("Created post visibility:", res.post.visibility);
        } catch (e) {}

        // Decide where to insert the new post based on its visibility (trim to avoid accidental whitespace mismatch)
        var container;
        var visibility =
          res.post && res.post.visibility ? res.post.visibility.trim() : "";

        if (
          visibility === "General" ||
          visibility === "Everyone" ||
          visibility === "Only Me" ||
          visibility === "Open for Rent"
        ) {
          container = $('.post-div[data-purpose="timeline"]');
        } else if (visibility === "Looking to Rent") {
          container = $('.post-div[data-purpose="looking"]');
        } else {
          // default to the first post-div (e.g., main feed)
          container = $(".post-div").first();
        }
        if (container && container.length) {
          container.prepend(_html);
        } else {
          // fallback: prepend to any post-div
          $(".post-div").prepend(_html);
        } //append new post to the top of feed

        // Clear the create post form so next time it's empty
        try {
          // Clear caption
          $("#post-caption").val("");
          // Clear file input and previews
          const fileInput = $("#post-thumbnail");
          if (fileInput.length) {
            fileInput.val("");
          }
          $("#preview_post_thumbnail").html("");
          // Reset visibility to default (General) and trigger change so item listing resets/hides
          $("#visibility").val("General").trigger("change");
          // Reset item listing select if present
          const itemSelect = $("#item-listings-select");
          if (itemSelect.length) {
            itemSelect.val("").prop("disabled", true).addClass("hidden");
            if (
              window.jQuery &&
              typeof itemSelect.selectpicker === "function"
            ) {
              try {
                itemSelect.selectpicker("refresh");
              } catch (e) {}
            }
          }
          // Reset dropdown-style listing (if present)
          const listingBtn = $("#select-item-listings");
          if (listingBtn.length) {
            $("#item-listings-dropdown").addClass("hidden");
            listingBtn.find("span:first").text("Select item listings");
            // hide the button itself so it won't appear for 'General' by mistake
            listingBtn.addClass("hidden");
            listingBtn.removeData("selected-id");
          }
          // Disable Post button and update styles
          $("#share-post")
            .prop("disabled", true)
            .addClass("opacity-50 cursor-not-allowed");
        } catch (e) {
          console.log("Error while clearing create post form:", e);
        }
      },
      error: function (xhr) {
        let message = "An error occurred. Please try again.";
        if (xhr && xhr.responseJSON && xhr.responseJSON.error) {
          message = xhr.responseJSON.error;
        }
        if (window.UIkit && typeof UIkit.notification === "function") {
          UIkit.notification({
            message: message,
            status: "danger",
            pos: "top-right",
            timeout: 4000,
          });
        } else {
          alert(message);
        }
      },
    });
  });

  // Disable/enable Post button based on caption content and show warning when disabled button clicked
  $(document).ready(function () {
    $("#post-form").each(function () {
      const $form = $(this);
      const $caption = $form.find("#post-caption");
      const $submit = $form.find("#share-post");

      function updateSubmitState() {
        if ($caption.length && $submit.length) {
          const hasText = $caption.val()
            ? $caption.val().trim().length > 0
            : false;
          $submit.prop("disabled", !hasText);
          if (!hasText) {
            $submit.addClass("opacity-50 cursor-not-allowed");
          } else {
            $submit.removeClass("opacity-50 cursor-not-allowed");
          }
        }
      }

      updateSubmitState();
      $caption.on("input", updateSubmitState);
    });

    // When a disabled share button is clicked, show a warning
    $(document).on("click", "#share-post:disabled", function (e) {
      e.preventDefault();
      if (window.UIkit && typeof UIkit.notification === "function") {
        UIkit.notification({
          message: "Please add a caption before posting.",
          status: "warning",
          pos: "top-right",
          timeout: 3000,
        });
      } else {
        alert("Please add a caption before posting.");
      }
      return false;
    });
  });

  //like post
  $(document).on("click", "#like-btn", function () {
    let btn_val = $(this).attr("data-like-btn");
    //console.log(btn_val); //fetch id from data-like-btn -> check index.html

    $.ajax({
      url: "/like_post/",
      dataType: "json",
      data: {
        id: btn_val, //fetch blk tgk atas console.log, id is from request.GET in views.py
      },
      success: function (response) {
        if (response.data.bool === true) {
          $("#like-count" + btn_val).text(response.data.likes);
          $(".like-btn" + btn_val).addClass("text-blue-500");
          $(".like-btn" + btn_val).removeClass("text-black");
        } else {
          $("#like-count" + btn_val).text(response.data.likes);
          $(".like-btn" + btn_val).addClass("text-black");
          $(".like-btn" + btn_val).removeClass("text-blue-500");
        }
      },
    });
  });

  //comment post
  $(document).on("click", "#comment-btn", function () {
    let id = $(this).attr("data-comment-btn");
    let comment = $("#comment-input" + id).val();
    console.log(id);
    console.log(comment);

    $.ajax({
      url: "/comment_post/",
      dataType: "json",
      data: {
        id: id,
        comment: comment,
      },
      success: function (response) {
        console.log(response);

        // Get current user ID from the DOM (we'll need to add this to the template)
        let currentUserId = $("#current-user-id").val();

        // Check if this comment belongs to the logged in user
        let deleteButtonHtml = "";
        if (response.data.user_id == currentUserId) {
          deleteButtonHtml =
            '<button class="ml-auto text-xs" id="delete-comment" data-delete-comment="' +
            response.data.comment_id +
            '"> \
                                <i class="fas fa-trash text-red-500"> </i>\
                              </button>';
        }

        let newComment =
          '<div class="flex card shadow p-2" id="comment-div' +
          response.data.comment_id +
          '">\
                        <div class="w-10 h-10 rounded-full relative flex-shrink-0">\
                            <img src=" ' +
          response.data.profile_image +
          '" alt="" class="absolute h-full rounded-full w-full">\
                        </div>\
                        <div>\
                            <div class="text-gray-700 py-2 px-3 rounded-md bg-gray-100 relative lg:ml-5 ml-2 lg:mr-12  dark:bg-gray-800 dark:text-gray-100 flex items-center">\
                                <p class="leading-6 flex-grow">' +
          response.data.comment +
          "</p>" +
          deleteButtonHtml +
          '\
                                <div class="absolute w-3 h-3 top-3 -left-1 bg-gray-100 transform rotate-45 dark:bg-gray-800"></div>\
                            </div>\
                            <div class="text-sm flex items-center space-x-3 mt-2 ml-5">\
                                <a id="like-comment-btn" data-like-comment="' +
          response.data.comment_id +
          '" class="like-comment' +
          response.data.comment_id +
          '" style="color: gray; cursor: pointer"> <i class="fas fa-heart"></i> </a> <small><span id="comment-likes-count' +
          response.data.comment_id +
          '">0</span></small>\
                                <details>\
                                    <summary><div class="">Reply</div></summary>\
                                    <details-menu role="menu" class="origin-topf-right relative right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focue:outline-none">\
                                        <div class="pfy-1" role="none">\
                                            <div class="p-1 d-flex">\
                                                <input type="text" class="with-border" name="" placeholder="Write Reply" id="reply-input' +
          response.data.comment_id +
          '">\
                                                <button id="reply-comment-btn" data-reply-comment-btn="' +
          response.data.comment_id +
          '" type="submit" class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900 data-reply-comment-btn' +
          response.data.comment_id +
          '" role="menuitem">\
                                                    <ion-icon name="send"></ion-icon>\
                                                </button>\
                                            </div>\
                                        </div>\
                                    </details-menu>\
                                </details>\
                                <span> <small> ' +
          response.data.date +
          ' ago </small> </span>\
                            </div>\
                            <div class="reply-div' +
          response.data.comment_id +
          '"></div>\
                        </div>\
                    </div>\
                    ';

        // Hide "No Comments Yet" message if it exists
        $("#comment-div" + id)
          .find('p:contains("No Comments Yet")')
          .closest(".flex")
          .hide();

        // Prepend the new comment
        $("#comment-div" + id).prepend(newComment);

        // Clear comment input after user submits comment
        $("#comment-input" + id).val("");

        // Update comment count
        $("#comment-count" + id).text(response.data.comment_count);

        // Show/Update "View All Comments" link if comment count > 2
        let viewAllDiv = $("#view-all-comments-" + id);
        if (response.data.comment_count > 2) {
          let viewAllLink =
            '<a href="/post/' +
            response.data.post_slug +
            '/" class="hover:text-blue-600 hover:underline"> View All ' +
            response.data.comment_count +
            " Comments</a>";
          viewAllDiv.html(viewAllLink);
        }
      },
    });
  });

  //like comment
  $(document).on("click", "#like-comment-btn", function () {
    let id = $(this).attr("data-like-comment");
    console.log("Comment id: ", id);

    //send ID back to dj server
    $.ajax({
      url: "/like_comment/",
      dataType: "json",
      data: {
        id: id,
      },
      success: function (response) {
        if (response.data.bool === true) {
          $("#comment-likes-count" + id).text(response.data.likes);
          $(".like-comment" + id).css("color", "red");
        } else {
          $("#comment-likes-count" + id).text(response.data.likes);
          $(".like-comment" + id).css("color", "gray");
        }
      },
    });
  });

  //reply comment
  $(document).on("click", "#reply-comment-btn", function () {
    let id = $(this).attr("data-reply-comment-btn");
    let reply = $("#reply-input" + id)
      .val()
      .trim();

    console.log(id);
    console.log(reply);

    // Validate that reply is not empty
    if (!reply || reply === "") {
      alert("Please write a reply before sending");
      return;
    }

    $.ajax({
      url: "/reply_comment/",
      dataType: "json",
      data: {
        id: id,
        reply: reply,
      },
      success: function (response) {
        let newReply =
          '<div class="flex mr-12 mb-2 mt-2" style="margin-right: 20px;">\
                    <div class="w-10 h-10 rounded-full relative flex-shrink-0">\
                        <img src="' +
          response.data.profile_image +
          '" style="width: 40px; height: 40px;" alt="" class="absolute h-full rounded-full w-full">\
                    </div>\
                    <div>\
                        <div class="text-gray-700 py-2 px-3 rounded-md bg-gray-100 relative lg:ml-5 ml-2 lg:mr-12 dark:bg-gray-800 dark:text-gray-100 flex items-center">\
                            <p class="leading-6 flex-grow">' +
          response.data.reply +
          '</p>\
                            <button class="ml-auto text-xs" id="delete-reply" data-delete-reply="' +
          response.data.reply_id +
          '">\
                                <i class="fas fa-trash text-red-500"></i>\
                            </button>\
                            <div class="absolute w-3 h-3 top-3 -left-1 bg-gray-100 transform rotate-45 dark:bg-gray-800"></div>\
                        </div>\
                        <div class="text-sm flex items-center space-x-3 mt-2 ml-5">\
                            <a id="like-reply-btn" data-like-reply="' +
          response.data.reply_id +
          '" class="like-reply' +
          response.data.reply_id +
          '" style="color: gray; cursor: pointer"> <i class="fas fa-heart"></i> </a>\
                            <small><span id="reply-likes-count' +
          response.data.reply_id +
          '">0</span></small>\
                        </div>\
                    </div>\
                </div>\
                ';
        $(".reply-div" + id).prepend(newReply);
        $("#reply-input" + id).val("");
      },
    });
  });

  //delete comment
  $(document).on("click", "#delete-comment", function () {
    let id = $(this).attr("data-delete-comment");
    console.log(id);

    $.ajax({
      url: "/delete_comment/",
      dataType: "json",
      data: {
        id: id,
      },
      success: function (response) {
        console.log("Comment ", id, " Deleted");

        // Get post_id from response
        let post_id = response.data.post_id;

        // Remove the comment completely from DOM
        $("#comment-div" + id).remove();

        // Update comment count
        let currentCount = parseInt($("#comment-count" + post_id).text()) || 0;
        let newCount = Math.max(0, currentCount - 1);
        $("#comment-count" + post_id).text(newCount);

        // Check if there are any remaining comments in this post's comment div
        let remainingComments = $("#comment-div" + post_id).find(
          ".flex.card.shadow"
        ).length;

        // If no comments remain, show "No Comments Yet" message
        if (remainingComments === 0) {
          let noCommentsHtml =
            '<div class="flex no-comments-msg">\
            <div>\
              <div class="text-gray-700 py-2 px-3 rounded-md bg-gray-100 relative lg:ml-5 ml-2 lg:mr-12 dark:bg-gray-800 dark:text-gray-100">\
                <p class="leading-6">No Comments Yet</p>\
              </div>\
            </div>\
          </div>';
          $("#comment-div" + post_id).prepend(noCommentsHtml);
        }
      },
    });
  });

  // Delete reply
  $(document).on("click", "#delete-reply", function () {
    let id = $(this).attr("data-delete-reply");
    console.log("Deleting reply:", id);

    $.ajax({
      url: "/delete_reply/",
      dataType: "json",
      data: {
        id: id,
      },
      success: function (response) {
        console.log("Reply ", id, " Deleted");

        // Remove the reply from DOM - find the parent flex container
        $("[data-delete-reply='" + id + "']")
          .closest(".flex.mr-12.mb-2.mt-2")
          .remove();

        UIkit.notification({
          message: "Reply deleted successfully",
          status: "success",
          pos: "top-right",
          timeout: 3000,
        });
      },
      error: function (err) {
        console.log(err);
        UIkit.notification({
          message: "Error deleting reply",
          status: "danger",
          pos: "top-right",
          timeout: 3000,
        });
      },
    });
  });

  // Like reply
  $(document).on("click", "#like-reply-btn", function () {
    let id = $(this).attr("data-like-reply");
    console.log("Reply id: ", id);

    $.ajax({
      url: "/like_reply/",
      dataType: "json",
      data: {
        id: id,
      },
      success: function (response) {
        if (response.data.bool === true) {
          $("#reply-likes-count" + id).text(response.data.likes);
          $(".like-reply" + id).css("color", "red");
        } else {
          $("#reply-likes-count" + id).text(response.data.likes);
          $(".like-reply" + id).css("color", "gray");
        }
      },
    });
  });

  //add friend
  $(document).on("click", "#add-friend", function () {
    let id = $(this).attr("data-friend-id");
    console.log("Added " + id + " as Friend");

    $.ajax({
      url: "/add-friend/",
      dataType: "json",
      data: {
        id: id,
      },
      success: function (response) {
        console.log(response);
        if (response.bool === true) {
          //alr sent friend request
          $("#friend-text").html(
            '<i class="fas fa-user-minus"></i> Cancel Request'
          );
          $(".add-friend" + id).addClass("bg-red-600");
          $(".add-friend" + id).removeClass("bg-blue-600");
        }
        if (response.bool === false) {
          //belum send
          $("#friend-text").html('<i class="fas fa-user-plus"></i> Add Friend');
          $(".add-friend" + id).addClass("bg-blue-600");
          $(".add-friend" + id).removeClass("bg-red-600");
        }
      },
    });
  });

  // UnFriend User
  $(document).on("click", "#unfriend", function () {
    let id = $(this).attr("data-unfriend");
    console.log(id);

    $.ajax({
      url: "/add-friend/",
      dataType: "json",
      data: {
        id: id,
      },
      success: function (response) {
        console.log(response);
        if (response.bool === true) {
          //alr sent friend request
          $("#unfriend-text").html(
            '<i class="fas fa-user-minus"></i> Unfriend'
          );
          $(".unfriend" + id).addClass("bg-red-600");
          $(".unfriend" + id).removeClass("bg-blue-600");
        }
        if (response.bool === false) {
          //belum send
          $("#unfriend-text").html(
            '<i class="fas fa-user-plus"></i> Add Friend'
          );
          $(".unfriend" + id).addClass("bg-blue-600");
          $(".unfriend" + id).removeClass("bg-red-600");
        }
      },
    });
  });

  // dropdown for Select Item Listings
  $(document).on("click", "#select-item-listings", function (e) {
    e.stopPropagation(); // prevent click from bubbling to document
    $("#item-listings-dropdown").toggleClass("hidden");
  });

  // Close dropdown if clicked outside
  $(document).on("click", function (e) {
    if (
      !$(e.target).closest("#select-item-listings").length &&
      !$(e.target).closest("#item-listings-dropdown").length
    ) {
      $("#item-listings-dropdown").addClass("hidden");
    }
  });

  // When user clicks an item in the item-listings dropdown, mark it as selected (ignore placeholder/no-value items)
  $(document).on("click", "#item-listings-dropdown li", function (e) {
    e.stopPropagation();
    const $li = $(this);
    const text = $li.text().trim();
    const val = $li.attr("data-value");

    function updateSelectedItemDetails(details) {
      const $panel = $("#item-listing-details");
      if (!$panel.length) return;
      if (!details || !details.title) {
        $panel.addClass("hidden");
        $panel.find("#item-details-title").text("");
        $panel.find("#item-details-description").text("");
        $panel.find("#item-details-location").text("");
        $panel.find("#item-details-rate").text("");
        $panel.find("#item-details-image").attr("src", "");
        return;
      }

      $panel.removeClass("hidden");
      $panel.find("#item-details-title").text(details.title || "");
      $panel.find("#item-details-description").text(details.description || "");
      $panel.find("#item-details-location").text(details.location || "");
      if (details.rate) {
        $panel.find("#item-details-rate").text("Daily rate: " + details.rate);
      } else {
        $panel.find("#item-details-rate").text("");
      }
      if (details.image) {
        $panel.find("#item-details-image").attr("src", details.image);
      } else {
        $panel.find("#item-details-image").attr("src", "");
      }
    }

    // ignore items that don't have a real data-value
    if (!val || val.toString().trim() === "") {
      updateSelectedItemDetails(null);
      return;
    }

    const $btn = $(this)
      .closest(".uk-modal-dialog, form")
      .find("#select-item-listings");
    if ($btn.length) {
      $btn.find("span:first").text(text || "Select item listings");
      $btn.data("selected-id", val);
      // close the dropdown
      $("#item-listings-dropdown").addClass("hidden");
    }

    updateSelectedItemDetails({
      title: text,
      description: $li.data("description") || "",
      location: $li.data("location") || "",
      rate: $li.data("daily-rate") || "",
      image: $li.data("image") || "",
    });
  });

  // Show/hide item-listing controls based on visibility select inside the same modal/form
  function updateListingControlsForVisibility($visibility) {
    const isOpen = $visibility.val() === "Open for Rent";
    const $container = $visibility.closest(".uk-modal-dialog, form");

    // an item exists if the select has a real option value or the dropdown has li[data-value]
    function containerHasItems() {
      const $itemSelect = $container.find("#item-listings-select");
      const $dropdown = $container.find("#item-listings-dropdown");
      if ($itemSelect.length) {
        const realOptions = $itemSelect.find("option").filter(function () {
          return $(this).val() && $(this).val().toString().trim() !== "";
        });
        if (realOptions.length) return true;
      }
      if ($dropdown.length) {
        const realItems = $dropdown.find("li[data-value]");
        if (realItems.length) return true;
      }
      return false;
    }

    const hasItems = containerHasItems();

    // select-style control
    const $itemSelect = $container.find("#item-listings-select");
    if ($itemSelect.length) {
      if (isOpen && hasItems) {
        $itemSelect.removeClass("hidden").prop("disabled", false);
      } else {
        $itemSelect.addClass("hidden").prop("disabled", true).val("");
        if (window.jQuery && typeof $itemSelect.selectpicker === "function") {
          try {
            $itemSelect.selectpicker("refresh");
          } catch (e) {}
        }
      }
    }

    // button-style control and placeholder for no-items
    const $listingBtn = $container.find("#select-item-listings");
    const $dropdown = $container.find("#item-listings-dropdown");

    // Ensure dropdown has placeholder when no items exist
    if ($dropdown.length && !$dropdown.find("li[data-value]").length) {
      // set placeholder item with empty data-value so click handler ignores it
      $dropdown.html(
        '<ul><li class="px-4 py-2 text-gray-500 cursor-default" data-value="">No item to be selected</li></ul>'
      );
    }

    if ($listingBtn.length) {
      if (isOpen) {
        // show button regardless of items; dropdown will show placeholder if empty
        $listingBtn.removeClass("hidden");
      } else {
        $listingBtn.addClass("hidden").removeData("selected-id");
        if ($dropdown.length) $dropdown.addClass("hidden");
        $listingBtn.find("span:first").text("Select item listings");
      }
    }
  }

  // Delegate change events for visibility selects so it works across all modals/pages
  $(document).on("change", "#visibility", function () {
    updateListingControlsForVisibility($(this));
  });

  // Initialize controls on page load for any existing visibility controls
  $(document).ready(function () {
    $("#visibility").each(function () {
      const $vis = $(this);
      updateListingControlsForVisibility($vis);

      // ensure dropdown-style listing has placeholder if empty
      const $container = $vis.closest(".uk-modal-dialog, form");
      const $dropdown = $container.find("#item-listings-dropdown");
      if ($dropdown.length && !$dropdown.find("li").length) {
        $dropdown.html(
          '<ul><li class="px-4 py-2 text-gray-500 cursor-default">No item to be selected</li></ul>'
        );
      }

      // Also ensure the no-items placeholder label exists if needed
      updateListingControlsForVisibility($vis);
    });

    // When the create-post modal is opened via the toggle, ensure listing controls reflect the current state and the form is reset
    $(document).on("click", '[uk-toggle*="#create-post-modal"]', function () {
      setTimeout(function () {
        const $modal = $("#create-post-modal");
        const $vis = $modal.find("#visibility");
        if ($vis.length) {
          // reset visibility to default and update controls
          $vis.val("General");
          updateListingControlsForVisibility($vis);
          try {
            if (window.jQuery && typeof $vis.selectpicker === "function") {
              $vis.selectpicker("refresh");
            }
          } catch (e) {}
        }
        // also clear caption and previews on open so modal always starts empty
        $modal.find("#post-caption").val("");
        $modal.find("#preview_post_thumbnail").html("");
        const $fileInput = $modal.find("#post-thumbnail");
        if ($fileInput.length) $fileInput.val("");
        // disable share button until user types
        $modal
          .find("#share-post")
          .prop("disabled", true)
          .addClass("opacity-50 cursor-not-allowed");
        // hide item details
        const $details = $modal.find("#item-listing-details");
        if ($details.length) {
          $details.addClass("hidden");
          $details.find("#item-details-title").text("");
          $details.find("#item-details-description").text("");
          $details.find("#item-details-location").text("");
          $details.find("#item-details-rate").text("");
          $details.find("#item-details-image").attr("src", "");
        }
      }, 60);
    });

    // Also listen to UIkit modal lifecycle events for extra robustness
    (function () {
      const modalEl = document.getElementById("create-post-modal");
      if (!modalEl) return;

      function resetCreatePostModal() {
        try {
          const $modal = $("#create-post-modal");
          const $vis = $modal.find("#visibility");
          if ($vis.length) {
            $vis.val("General");
            updateListingControlsForVisibility($vis);
            try {
              if (window.jQuery && typeof $vis.selectpicker === "function") {
                $vis.selectpicker("refresh");
              }
            } catch (e) {}
          }
          $modal.find("#post-caption").val("");
          $modal.find("#preview_post_thumbnail").html("");
          const $fileInput = $modal.find("#post-thumbnail");
          if ($fileInput.length) $fileInput.val("");
          $modal
            .find("#share-post")
            .prop("disabled", true)
            .addClass("opacity-50 cursor-not-allowed");
          // hide listing button if visible
          const $listingBtn = $modal.find("#select-item-listings");
          if ($listingBtn.length) {
            $listingBtn.addClass("hidden");
            $listingBtn.removeData("selected-id");
          }
          const $itemSelect = $modal.find("#item-listings-select");
          if ($itemSelect.length) {
            $itemSelect.val("").prop("disabled", true).addClass("hidden");
            try {
              if (
                window.jQuery &&
                typeof $itemSelect.selectpicker === "function"
              )
                $itemSelect.selectpicker("refresh");
            } catch (e) {}
          }
          const $details = $("#item-listing-details");
          if ($details.length) {
            $details.addClass("hidden");
            $details.find("#item-details-title").text("");
            $details.find("#item-details-description").text("");
            $details.find("#item-details-location").text("");
            $details.find("#item-details-rate").text("");
            $details.find("#item-details-image").attr("src", "");
          }
        } catch (e) {
          console.log("Error resetting create post modal:", e);
        }
      }

      modalEl.addEventListener("beforeshow", function () {
        resetCreatePostModal();
      });

      modalEl.addEventListener("show", function () {
        resetCreatePostModal();
      });

      // Also ensure reset when the modal is closed so no stale state remains
      modalEl.addEventListener("hidden", function () {
        resetCreatePostModal();
      });
    })();
  });
});
