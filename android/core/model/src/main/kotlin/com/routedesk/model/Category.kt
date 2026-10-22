package com.routedesk.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
enum class Category(val displayName: String, val code: String) {
    @SerialName("access")
    ACCESS("Access & Identity", "access"),

    @SerialName("hardware")
    HARDWARE("Hardware & Equipment", "hardware"),

    @SerialName("software")
    SOFTWARE("Software & Tools", "software"),

    @SerialName("network")
    NETWORK("Network & Connectivity", "network"),

    @SerialName("hr_operations")
    HR_OPERATIONS("HR Operations", "hr_operations"),

    @SerialName("facilities")
    FACILITIES("Facilities & Workplace", "facilities"),

    @SerialName("security")
    SECURITY("Security & Compliance", "security"),

    @SerialName("billing_purchase")
    BILLING_PURCHASE("Billing & Purchasing", "billing_purchase");

    companion object {
        fun fromCode(code: String): Category =
            entries.firstOrNull { it.code.equals(code, ignoreCase = true) } ?: SOFTWARE
    }
}
