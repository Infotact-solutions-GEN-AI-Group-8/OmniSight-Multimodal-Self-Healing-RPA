from playwright.sync_api import sync_playwright


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)

    page = browser.new_page(
        viewport={"width": 1440, "height": 900}
    )

    try:
        # Step 1: Open the website
        page.goto(
            "https://omnisight-mock-website.vercel.app",
            wait_until="domcontentloaded",
            timeout=60000
        )
        page.wait_for_timeout(2000)

        print("Website opened:", page.url)
        print("Title:", page.title())

        # Step 2: Open product 41
        page.locator(
            '[data-go="#/product/41"]'
        ).first.click()
        page.wait_for_timeout(1000)

        print("Product page opened:", page.url)

        # Step 3: Add product to cart
        page.locator(
            'button[data-add="41"]'
        ).click()
        page.wait_for_timeout(1000)

        print("Product added to cart.")

        # Step 4: Open cart
        page.locator(
            'a[href="#/cart"]'
        ).click()
        page.wait_for_timeout(1000)

        print("Cart opened:", page.url)

        # Step 5: Proceed to checkout
        page.locator(
            'button[data-go="#/checkout"]'
        ).click()
        page.wait_for_timeout(1000)

        print("Checkout opened:", page.url)

        # Step 6: Fill customer details
        page.locator(
            'input[name="name"]'
        ).fill("Test Customer")

        page.locator(
            'input[name="phone"]'
        ).fill("9000000000")

        page.locator(
            'input[name="email"]'
        ).fill("test.customer@example.com")

        page.locator(
            "textarea"
        ).fill("123 Test Street")

        page.locator(
            'input[name="city"]'
        ).fill("Ahmedabad")

        page.locator(
            'input[name="pin"]'
        ).fill("380001")

        # Select state if a dropdown exists
        state_select = page.locator("select:visible")

        if state_select.count() > 0:
            try:
                state_select.first.select_option(
                    label="Gujarat"
                )
            except Exception:
                print("State selection left unchanged.")

        page.screenshot(
            path="01_customer_details.png",
            full_page=True
        )

        # Step 7: Continue to payment
        page.get_by_role(
            "button",
            name="Continue to payment"
        ).click()

        page.wait_for_timeout(1500)

        print("Payment page opened:", page.url)

        page.screenshot(
            path="02_payment_page.png",
            full_page=True
        )

        # Step 8: Find and select Cash on Delivery
        print("\nLooking for Cash on Delivery...")

        cod_selected = False

        # Try radio buttons whose labels mention COD
        radio_buttons = page.locator(
            'input[type="radio"]:visible'
        )

        for i in range(radio_buttons.count()):
            radio = radio_buttons.nth(i)

            radio_name = (
                radio.get_attribute("name") or ""
            ).lower()

            radio_value = (
                radio.get_attribute("value") or ""
            ).lower()

            radio_id = (
                radio.get_attribute("id") or ""
            ).lower()

            details = " ".join([
                radio_name,
                radio_value,
                radio_id
            ])

            if any(
                word in details
                for word in ["cod", "cash", "delivery"]
            ):
                radio.check()
                cod_selected = True
                break

        # If the radio button has no useful attributes,
        # try the visible Cash on Delivery label.
        if not cod_selected:
            cod_text = page.get_by_text(
                "Cash on Delivery",
                exact=False
            ).first

            if cod_text.count() > 0:
                try:
                    cod_text.click(timeout=3000)
                    cod_selected = True
                except Exception:
                    pass

        if cod_selected:
            print("Cash on Delivery option selected.")
        else:
            print(
                "Could not identify a COD option automatically."
            )

        page.wait_for_timeout(1000)

        page.screenshot(
            path="03_cod_selected.png",
            full_page=True
        )

        # Step 9: Inspect available buttons
        print("\n--- Payment buttons ---")

        buttons = page.locator("button:visible")

        for i in range(buttons.count()):
            button = buttons.nth(i)

            print(
                f"Button {i}: "
                f"{button.inner_text().strip()!r} | "
                f"{button.evaluate('(el) => el.outerHTML')}"
            )

        # Step 10: Place the order if a matching
        # final-order button is available.
        order_button_names = [
            "Place order",
            "Place Order",
            "Confirm order",
            "Confirm Order",
            "Complete order",
            "Complete Order",
            "Pay on delivery",
            "Order now"
        ]

        order_placed_attempt = False

        for button_name in order_button_names:
            candidate = page.get_by_role(
                "button",
                name=button_name,
                exact=True
            )

            if candidate.count() > 0:
                visible_candidate = candidate.first

                if visible_candidate.is_visible():
                    print(
                        "Clicking final-order button:",
                        button_name
                    )

                    visible_candidate.click()
                    page.wait_for_timeout(2000)

                    order_placed_attempt = True
                    break

        if not order_placed_attempt:
            print(
                "\nNo recognized final-order button found. "
                "Inspect the printed buttons before proceeding."
            )

        # Step 11: Capture the resulting page
        print("\nFinal page URL:", page.url)
        print("Page title:", page.title())

        page.screenshot(
            path="04_order_result.png",
            full_page=True
        )

        print("\nVisible confirmation text:")

        body_text = page.locator("body").inner_text()
        print(body_text[:3000])

        print(
            "\nCheck the page output to confirm whether the "
            "mock website actually accepted the order."
        )

        page.wait_for_timeout(5000)

    except Exception as error:
        print("\nAutomation failed:", error)

        try:
            page.screenshot(
                path="automation_error.png",
                full_page=True
            )
        except Exception:
            pass

    finally:
        browser.close()
        print("Browser closed.")
